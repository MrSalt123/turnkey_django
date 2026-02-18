import csv
import re
from django.contrib import admin
from django.http import HttpResponse
from django.db.models import Case, When
from .models import (
    TKResources, Status, Framework, FrameworkRequirement, 
    InternalControl, Audit, AuditAssessment, Finding
)

def natural_sort_key(code, fw_name):
    fw_name = fw_name.upper()
    code = str(code)
    fw_priority = 0 if "SOC2" in fw_name else 1
    soc2_prefix_map = {'CC': 0, 'A': 1, 'C': 2, 'P': 3, 'PI': 3}
    
    match = re.match(r'^([a-zA-Z]+)(.*)', code)
    if match:
        prefix, rest = match.groups()
        prefix_priority = soc2_prefix_map.get(prefix.upper(), 99)
    else:
        prefix_priority = 99
        rest = code

    num_parts = [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', rest) if s]
    return (fw_priority, prefix_priority, num_parts)

@admin.register(FrameworkRequirement)
class FrameworkRequirementAdmin(admin.ModelAdmin):
    list_display = ('code', 'short_description', 'framework', 'parent')
    search_fields = ('code', 'short_description') 
    list_filter = ('framework',)
    autocomplete_fields = ['parent']
    actions = ['export_mapping_to_csv']

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('framework', 'parent')
        req_list = list(qs)
        req_list.sort(key=lambda x: natural_sort_key(x.code, x.framework.name))
        
        preserved_ids = [r.pk for r in req_list]
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(preserved_ids)])
        return qs.filter(pk__in=preserved_ids).order_by(preserved)

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        referring_model = request.GET.get('model_name')
        if referring_model == 'frameworkrequirement':
            queryset = queryset.filter(parent__isnull=True)
        return queryset, use_distinct

    @admin.action(description="Export selected Requirements & Controls to CSV")
    def export_mapping_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="compliance_mapping.csv"'
        
        writer = csv.writer(response)
        # Updated Headers: Added Long Description, Removed Parent Code and Control Description
        writer.writerow([
            'Framework', 
            'Req Code', 
            'Short Description', 
            'Long Description', 
            'Control Codes',
            'Is Parent' # Placeholder for your highlighting logic
        ])

        # Optimize query and apply natural sort
        req_list = list(queryset.select_related('framework', 'parent').prefetch_related('controls', 'sub_requirements'))
        req_list.sort(key=lambda x: natural_sort_key(x.code, x.framework.name))

        for req in req_list:
            all_controls = req.controls.all()
            
            # Logic to check if it's a parent (has sub-requirements)
            is_parent = req.sub_requirements.exists()
            parent_label = "YES (Parent)" if is_parent else ""

            # Formatting Control Codes with newlines instead of commas
            # Excel/Google Sheets will display these on new lines within the cell
            control_codes_str = "\n".join([c.code for c in all_controls]) if all_controls.exists() else "No Control Mapped"
            
            writer.writerow([
                req.framework.name, 
                req.code, 
                req.short_description,
                req.long_description,
                control_codes_str,
                parent_label
            ])
                
        return response

# Standard Registrations
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

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    search_fields = ('status_name', 'type')

admin.site.register(Framework)
admin.site.register(Finding)
