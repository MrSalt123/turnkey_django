import os
import pandas as pd
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grc_tool.settings')
django.setup()

from core.models import FrameworkRequirement, Framework

def import_soc2_requirements(file_path, framework_name="SOC2"):
    # Load framework object
    framework, _ = Framework.objects.get_or_create(name=framework_name)
    
    # Read Excel - Assuming columns are: 0: TSC Ref, 1: Criteria 1, 2: Criteria 2, 3: Points of Focus
    df = pd.read_excel(file_path)
    
    for _, row in df.iterrows():
        parent_code = str(row[0]).strip() # CC1.1
        short_desc = str(row[2]).strip()  # First Criteria column
        long_desc = str(row[3]).strip()   # Second Criteria column
        points_of_focus = str(row[4]).strip() # Points of Focus column

        # 1. Create or Update Parent (e.g., CC1.1)
        parent, created = FrameworkRequirement.objects.update_or_create(
            code=parent_code,
            framework=framework,
            defaults={
                'short_description': short_desc,
                'long_description': long_desc,
                'parent': None
            }
        )

        # 2. Process Point of Focus (Sub-requirement)
        if points_of_focus and " - " in points_of_focus:
            # Split at the first occurrence of " - "
            sub_short, sub_long = points_of_focus.split(" - ", 1)
            
            # Create a unique code for the sub-requirement (e.g., CC1.1.1)
            # You may need a counter or logic to increment the last digit
            existing_subs = FrameworkRequirement.objects.filter(parent=parent).count()
            sub_code = f"{parent_code}.{existing_subs + 1}"

            FrameworkRequirement.objects.get_or_create(
                code=sub_code,
                framework=framework,
                parent=parent,
                defaults={
                    'short_description': sub_short.strip(),
                    'long_description': sub_long.strip()
                }
            )

if __name__ == "__main__":
    import_soc2_requirements('soc2_data.xlsx')
    print("Import Complete!")
