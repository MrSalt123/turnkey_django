import csv
from django.core.management.base import BaseCommand
from core.models import Framework, FrameworkRequirement, InternalControl

class Command(BaseCommand):
    help = 'Export Frameworks, Requirements, and Control mappings to CSV'

    def handle(self, *args, **options):
        filename = 'compliance_mapping_export.csv'
        
        # Define the headers for the CSV
        headers = [
            'Framework Name', 
            'Requirement Code', 
            'Requirement Description', 
            'Control Code', 
            'Control Short Description', 
            'Workpaper Ref'
        ]

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)

                # Iterate through Requirements to ensure we catch those without controls too
                requirements = FrameworkRequirement.objects.select_related('framework').prefetch_related('controls').all()

                for req in requirements:
                    controls = req.controls.all()
                    
                    if controls:
                        for control in controls:
                            writer.writerow([
                                req.framework.name,
                                req.code,
                                req.short_description,
                                control.code,
                                control.short_description,
                                control.wp_ref
                            ])
                    else:
                        # Case where a requirement exists but no control is mapped yet
                        writer.writerow([
                            req.framework.name,
                            req.code,
                            req.short_description,
                            'N/A',
                            'No Control Mapped',
                            'N/A'
                        ])

            self.stdout.write(self.style.SUCCESS(f'Successfully exported data to {filename}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Export failed: {str(e)}'))
