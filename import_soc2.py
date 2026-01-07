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
    
    # 2. Robust CSV Loading
    # We skip the title row, force comma separator, and handle multi-line cells
    try:
        df = pd.read_csv(
            file_path, 
            skiprows=1, 
            sep=',', 
            quotechar='"', 
            encoding='utf-8-sig'
        )
    except Exception:
        df = pd.read_csv(file_path, skiprows=1, sep=',', encoding='latin-1')

    # Clean header names to remove invisible spaces
    df.columns = [c.strip() for c in df.columns]

    print(f"Importing requirements into {framework_name}...")

    for index, row in df.iterrows():
        # We only pull the columns needed for the requirement hierarchy
        tsc_ref = str(row.get('TSC Ref. #', '')).strip()
        category = str(row.get('Criteria Category', '')).strip()
        criteria = str(row.get('Criteria', '')).strip()
        points_of_focus = str(row.get('Points of Focus', '')).strip()

        # Skip rows that are empty or just header artifacts
        if not tsc_ref or tsc_ref.lower() == 'nan':
            continue

        # 3. Create or Update the Parent Requirement (e.g., CC1.1)
        # We use 'update_or_create' so that multiple rows with the same CC code 
        # point to the same parent object.
        parent, created = FrameworkRequirement.objects.update_or_create(
            code=tsc_ref,
            framework=framework,
            defaults={
                'short_description': category, # e.g., CONTROL ENVIRONMENT
                'long_description': criteria,   # e.g., COSO Principle 1...
            }
        )

        # 4. Process the Point of Focus into a Sub-Requirement
        # Check for the dash/separator in the Point of Focus
        delimiter = "—" if "—" in points_of_focus else " - "
        
        if points_of_focus and points_of_focus.lower() != 'nan':
            # Split into title and description if a dash exists
            if delimiter in points_of_focus:
                sub_title, sub_body = points_of_focus.split(delimiter, 1)
                sub_title = sub_title.strip()
                sub_body = sub_body.strip()
            else:
                sub_title = points_of_focus.strip()
                sub_body = ""

            # Only create if this specific point of focus hasn't been added yet
            if not FrameworkRequirement.objects.filter(parent=parent, short_description=sub_title).exists():
                # Count current sub-requirements for this parent to set the code (CC1.1.1, etc)
                current_subs = FrameworkRequirement.objects.filter(parent=parent).count()
                sub_code = f"{tsc_ref}.{current_subs + 1}"

                FrameworkRequirement.objects.create(
                    code=sub_code,
                    framework=framework,
                    parent=parent,
                    short_description=sub_title,
                    long_description=sub_body
                )
                print(f"  [Added] {sub_code}: {sub_title[:40]}...")

if __name__ == "__main__":
    import_soc2_requirements('soc2_data.csv')
    print("\n--- SOC 2 Hierarchy Import Complete ---")
