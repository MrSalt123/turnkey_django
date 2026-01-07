import pandas as pd
import os
import django
import csv

# 1. Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grc_tool.settings')
django.setup()

from core.models import FrameworkRequirement, Framework

def import_soc2_requirements(file_path, framework_name="SOC2"):
    # Load or create the framework
    framework, _ = Framework.objects.get_or_create(name=framework_name)
    
    # 2. Load the CSV
    # We use 'utf-8-sig' to handle Excel's potential hidden characters
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    except Exception:
        # Fallback to latin-1 if utf-8 fails
        df = pd.read_csv(file_path, encoding='latin-1')

    # Clean header names
    df.columns = [c.strip() for c in df.columns]

    print(f"--- Starting SOC 2 Import from {file_path} ---")

    for index, row in df.iterrows():
        # Using exact column names from your cleaned file
        tsc_ref = str(row.get('TSC Ref.', '')).strip()
        category = str(row.get('Criteria Category', '')).strip()
        criteria = str(row.get('Criteria', '')).strip()
        focus = str(row.get('Points of Focus', '')).strip()

        # Skip empty rows
        if not tsc_ref or tsc_ref.lower() == 'nan':
            continue

        # 3. Create or Update the Parent Requirement (e.g., CC1.1)
        # category -> short_description (Title)
        # criteria -> long_description (COSO detail)
        parent, created = FrameworkRequirement.objects.update_or_create(
            code=tsc_ref,
            framework=framework,
            defaults={
                'short_description': category,
                'long_description': criteria,
                'parent': None
            }
        )

        # 4. Process the Point of Focus (Sub-requirement)
        # Splitting on the em-dash (—) or standard dash (-)
        delimiter = "—" if "—" in focus else " - "
        
        if focus and focus.lower() != 'nan':
            if delimiter in focus:
                sub_title, sub_body = focus.split(delimiter, 1)
                sub_title = sub_title.strip()
                sub_body = sub_body.strip()
            else:
                sub_title = focus.strip()
                sub_body = ""

            # Check if this specific point of focus already exists for this parent
            if not FrameworkRequirement.objects.filter(parent=parent, short_description=sub_title).exists():
                # Generate sub-code based on count (e.g., CC1.1.1, CC1.1.2)
                current_subs = FrameworkRequirement.objects.filter(parent=parent).count()
                sub_code = f"{tsc_ref}.{current_subs + 1}"

                FrameworkRequirement.objects.create(
                    code=sub_code,
                    framework=framework,
                    parent=parent,
                    short_description=sub_title,
                    long_description=sub_body
                )
                print(f"  [Created] {sub_code}: {sub_title[:50]}...")

if __name__ == "__main__":
    # Ensure this matches your final file name
    import_soc2_requirements('soc2_data.csv')
    print("\n--- SOC 2 Import Complete ---")
