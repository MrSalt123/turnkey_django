import os
import pandas as pd
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grc_tool.settings')
django.setup()

from core.models import FrameworkRequirement, Framework

def import_soc2_requirements(file_path, framework_name="SOC2"):
    framework, _ = Framework.objects.get_or_create(name=framework_name)
    
    # skiprows=2 ignores the first two title/header rows
    # header=0 tells pandas that the 3rd row (index 2) is the actual header
    df = pd.read_excel(file_path, skiprows=2)
    
    for _, row in df.iterrows():
        # Skip row if the first column (TSC Ref) is empty
        if pd.isna(row.iloc[0]):
            continue

        try:
            parent_code = str(row.iloc[0]).strip()   # CC1.1
            short_desc = str(row.iloc[2]).strip()    # CONTROL ENVIRONMENT
            long_desc = str(row.iloc[3]).strip()     # COSO Principle 1...
            points_of_focus = str(row.iloc[4]).strip() # Points of Focus
            
            # 1. Create or Update Parent
            parent, created = FrameworkRequirement.objects.update_or_create(
                code=parent_code,
                framework=framework,
                defaults={
                    'short_description': short_desc,
                    'long_description': long_desc,
                    'parent': None
                }
            )

            # 2. Process Point of Focus
            # Using "—" (em-dash) or "-" (hyphen) based on your screenshot's formatting
            delimiter = "—" if "—" in points_of_focus else "-"
            
            if points_of_focus and delimiter in points_of_focus:
                sub_short, sub_long = points_of_focus.split(delimiter, 1)
                
                # Logic to prevent duplicate sub-requirements if re-running script
                existing_subs_count = FrameworkRequirement.objects.filter(
                    parent=parent, 
                    short_description=sub_short.strip()
                ).count()

                if existing_subs_count == 0:
                    total_subs = FrameworkRequirement.objects.filter(parent=parent).count()
                    sub_code = f"{parent_code}.{total_subs + 1}"

                    FrameworkRequirement.objects.get_or_create(
                        code=sub_code,
                        framework=framework,
                        parent=parent,
                        defaults={
                            'short_description': sub_short.strip(),
                            'long_description': sub_long.strip()
                        }
                    )
        except IndexError as e:
            print(f"Skipping row due to missing columns: {e}")
            continue

if __name__ == "__main__":
    import_soc2_requirements('soc2_data.xlsx')
    print("Import Complete!")
