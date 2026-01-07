import pandas as pd
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grc_tool.settings')
django.setup()

from core.models import FrameworkRequirement, Framework

def import_soc2_requirements(file_path, framework_name="SOC2"):
    # Load framework object
    framework, _ = Framework.objects.get_or_create(name=framework_name)
    
    # Read CSV - Use 'header=0' to ensure the first row is treated as column names
    df = pd.read_csv(file_path)

    # Clean up column names (removes hidden spaces or newlines)
    df.columns = [c.strip() for c in df.columns]

    for index, row in df.iterrows():
        # 1. Extract data using exact column names from your file
        # If the column name is exactly "Criteria" twice, Pandas names them "Criteria" and "Criteria.1"
        tsc_ref = str(row.get('TSC Ref. #', '')).strip()
        criteria_1 = str(row.get('Criteria', '')).strip()
        # In multi-column "Criteria", pandas usually appends .1, .2 etc.
        criteria_2 = str(row.get('Criteria.1', '')).strip() 
        points_of_focus = str(row.get('Points of Focus', '')).strip()

        # Skip rows that don't have a TSC Ref (like empty rows at the bottom)
        if not tsc_ref or tsc_ref == 'nan':
            continue

        # 2. Create or Update Parent (e.g., CC1.1)
        parent, created = FrameworkRequirement.objects.update_or_create(
            code=tsc_ref,
            framework=framework,
            defaults={
                'short_description': criteria_1,
                'long_description': criteria_2,
                'parent': None
            }
        )

        # 3. Process Point of Focus (Sub-requirement)
        # Your file uses both "—" (em-dash) and "-" (hyphen). Let's handle both.
        delimiter = None
        if "—" in points_of_focus:
            delimiter = "—"
        elif " - " in points_of_focus:
            delimiter = " - "

        if delimiter:
            sub_short, sub_long = points_of_focus.split(delimiter, 1)
            
            # Check if this sub-req already exists to avoid duplicates on re-run
            existing_count = FrameworkRequirement.objects.filter(
                parent=parent, 
                short_description=sub_short.strip()
            ).count()

            if existing_count == 0:
                total_subs = FrameworkRequirement.objects.filter(parent=parent).count()
                sub_code = f"{tsc_ref}.{total_subs + 1}"

                FrameworkRequirement.objects.create(
                    code=sub_code,
                    framework=framework,
                    parent=parent,
                    short_description=sub_short.strip(),
                    long_description=sub_long.strip()
                )
                print(f"Created sub-requirement: {sub_code}")

if __name__ == "__main__":
    # Use the filename of the CSV you uploaded
    import_soc2_requirements('soc2_data.xlsx - ISO 270012022.csv')
    print("Import Complete!")
