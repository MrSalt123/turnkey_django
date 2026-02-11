from django.contrib import admin
from .models import TKResources, Status, Framework, FrameworkRequirement, InternalControl, Audit, AuditAssessment, Finding

from django.http import HttpResponse
import csv
from .models import FrameworkRequirement

@admin.register(TKResources)
class TKResourcesAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email')
    search_fields = ('first_name', 'last_name', 'email')

@admin.register(InternalControl)
class InternalControlAdmin(admin.ModelAdmin):
    list_display = ('code', 'short_description', 'wp_ref')
    search_fields = ('wp_ref', 'short_description')
    autocomplete_fields = ['requirements']

@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = ('name', 'fiscal_year')
    search_fields = ('name',)

@admin.register(AuditAssessment)
class AuditAssessmentAdmin(admin.ModelAdmin):
    list_display = ('audit', 'control', 'status', 'tester')
    autocomplete_fields = ['control', 'tester', 'reviewer', 'audit']

@admin.register(FrameworkRequirement)
class FrameworkRequirementAdmin(admin.ModelAdmin):
    list_display = ('code', 'short_description', 'framework', 'parent')
    search_fields = ('code', 'short_description') 
    list_filter = ('framework',)
    autocomplete_fields = ['parent']

    actions = ['export_mapping_to_csv']

    @admin.action(description="Export selected Requirements & Controls to CSV")
    def export_mapping_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="compliance_mapping.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Framework', 'Req Code', 'Req Description', 
            'Parent Code', 'Control Code', 'Control Description'
        ])

        # prefetch_related('controls') is CRITICAL here for performance
        queryset = queryset.select_related('framework', 'parent').prefetch_related('controls')

        for req in queryset:
            # Fetch all controls for THIS specific requirement
            all_mapped_controls = req.controls.all()
            
            if all_mapped_controls.exists():
                for control in all_mapped_controls:
                    # This loop ensures every control gets its own row
                    writer.writerow([
                        req.framework.name,
                        req.code,
                        req.short_description,
                        req.parent.code if req.parent else "None",
                        control.code,
                        control.short_description
                    ])
            else:
                # Still include the requirement if it has 0 controls
                writer.writerow([
                    req.framework.name,
                    req.code,
                    req.short_description,
                    req.parent.code if req.parent else "None",
                    "No Control Mapped",
                    "N/A"
                ])
                
        return response

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        
        # Determine the source of the search request
        # 'model_name' tells us which page the user is currently on
        referring_model = request.GET.get('model_name')

        if referring_model == 'frameworkrequirement':
            # We are on the Requirement page: Only show Top-Level Parents
            queryset = queryset.filter(parent__isnull=True)
        
        # If referring_model is 'internalcontrol', we don't filter.
        # This allows you to see both CC6.1 AND 6.1.1 (the Points of Focus).
            
        return queryset, use_distinct

# Register the rest
@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    search_fields = ('status_name', 'type')

admin.site.register(Framework)
admin.site.register(Finding)
