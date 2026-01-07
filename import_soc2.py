import pandas as pd
import os
import django

# 1. Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grc_tool.settings')
django.setup()

from core.models import FrameworkRequirement, Framework

def import_soc2_requirements(file_path, framework_name="SOC2"):
    # Load or create the framework
    framework, _ = Framework.objects.get_or_create(name=framework_name)
    
    # 2. Load CSV - skipping the first title row
    # Using 'utf-8-sig' to handle potential Excel BOM (Byte Order Mark)
    try:
        df = pd.read_csv(file_path, skiprows=1, encoding='utf-8-sig')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, skiprows=1, encoding='latin-1')

    # Clean column names
    df.columns = [c.strip() for c in df.columns]

    print(f"Starting import from {file_path}...")

    for index, row in df.iterrows():
        # Map columns based on the CSV structure
        tsc_ref = str(row.get('TSC Ref. #', '')).strip()
        category = str(row.get('Criteria Category', '')).strip()
        criteria = str(row.get('Criteria', '')).strip()
        points_of_focus = str(row.get('Points of Focus', '')).strip()

        # Skip empty rows
        if not tsc_ref or tsc_ref.lower() == 'nan':
            continue

        # 3. Create or Update the Parent (e.g., CC1.1)
        # category (CONTROL ENVIRONMENT) goes to short_description
        # criteria (COSO Principle 1...) goes to long_description
        parent, created = FrameworkRequirement.objects.update_or_create(
            code=tsc_ref,
            framework=framework,
            defaults={
                'short_description': category,
                'long_description': criteria,
                'parent': None
            }
        )

        # 4. Process the Point of Focus into a Sub-Requirement
        # Your CSV uses the em-dash "—" as a separator
        delimiter = "—" if "—" in points_of_focus else " - "
        
        if points_of_focus and delimiter in points_of_focus:
            sub_short, sub_long = points_of_focus.split(delimiter, 1)
            sub_short = sub_short.strip()
            sub_long = sub_long.strip()

            # We check if this specific point of focus already exists for this parent
            # to avoid creating duplicates if you run the script again
            if not FrameworkRequirement.objects.filter(parent=parent, short_description=sub_short).exists():
                # Count current sub-requirements to generate code (e.g., CC1.1.1, CC1.1.2)
                current_count = FrameworkRequirement.objects.filter(parent=parent).count()
                sub_code = f"{tsc_ref}.{current_count + 1}"

                FrameworkRequirement.objects.create(
                    code=sub_code,
                    framework=framework,
                    parent=parent,
                    short_description=sub_short,
                    long_description=sub_long
                )
                print(f"  Added Sub-Requirement: {sub_code}")
        else:
            # If there's no dash, we treat the whole field as the short description
            if points_of_focus and not FrameworkRequirement.objects.filter(parent=parent, short_description=points_of_focus).exists():
                current_count = FrameworkRequirement.objects.filter(parent=parent).count()
                sub_code = f"{tsc_ref}.{current_count + 1}"
                FrameworkRequirement.objects.create(
                    code=sub_code,
                    framework=framework,
                    parent=parent,
                    short_description=points_of_focus,
                    long_description=""
                )

if __name__ == "__main__":
    import_soc2_requirements('soc2_data.csv')
    print("\n--- SOC2 Import Complete ---")
