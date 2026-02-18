import uuid
from django.db import models

class TKResources(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Status(models.Model):
    type = models.CharField(max_length=100) # Audits, Findings
    status_name = models.CharField(max_length=100) # In progress, complete, etc.

    def __str__(self):
        return f"{self.type}: {self.status_name}"

class Framework(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class FrameworkRequirement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='sub_requirements'
    )

    code = models.CharField(max_length=50)
    short_description = models.TextField()
    long_description = models.TextField()

    def __str__(self):
        return f"{self.code}: {self.short_description[:30]}"

class InternalControl(models.Model):
    CATEGORY_CHOICES = [
        ('AC', 'Access Control'),
        ('AV', 'Availability'),
        ('SP', 'Security Plan'),
        ('AM', 'Asset Management'),
        ('SM', 'System Monitoring'),
        ('PS', 'Physical Security'),
        ('KM', 'Contract Management'),
        ('RM', 'Risk Management'),
        ('IR', 'Incident Response'),
        ('HR', 'Human Resources'),
        ('CM', 'Change Management'),
        ('CO', 'Confidentiality'),
        ('CE', 'Control Environment'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=2, choices=CATEGORY_CHOICES, null=True, blank=True)
    short_description = models.TextField()
    long_description = models.TextField()
    test_procedures = models.TextField()
    wp_ref = models.CharField(max_length=255, verbose_name="Workpaper Reference")

    requirements = models.ManyToManyField(FrameworkRequirement, related_name='controls')

    def __str__(self):
        return f"{self.code}: {self.short_description[:50]}"

class Audit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    fiscal_year = models.IntegerField()

    def __str__(self):
        return f"{self.name} ({self.fiscal_year})"

class AuditAssessment(models.Model):
    CONCLUSION_CHOICES = [
        ('NO_EXC', 'No Exceptions Noted'),
        ('EXC_UNREM', 'Exception Noted (Unremediated)'),
        ('EXC_REM', 'Exception Noted (Remediated)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE)
    control = models.ForeignKey(InternalControl, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, on_delete=models.CASCADE)

    tester = models.ForeignKey(TKResources, on_delete=models.SET_NULL, null=True, related_name="tested_assessments")
    reviewer = models.ForeignKey(TKResources, on_delete=models.SET_NULL, null=True, related_name="reviewed_assessments")
    tester_so = models.ForeignKey(TKResources, on_delete=models.SET_NULL, null=True, related_name="tester_signoffs")
    primary_reviewer_so = models.ForeignKey(TKResources, on_delete=models.SET_NULL, null=True, related_name="primary_signoffs")
    secondary_reviewer_so = models.ForeignKey(TKResources, on_delete=models.SET_NULL, null=True, related_name="secondary_signoffs")

    tod_result = models.TextField()
    toe_result = models.TextField()
    conclusion = models.CharField(max_length=50, choices=CONCLUSION_CHOICES)
    comments = models.TextField(blank=True)

class Finding(models.Model):
    CATEGORY_CHOICES = [('Finding', 'Finding'), ('Observation', 'Observation')]
    PRIORITY_CHOICES = [('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(AuditAssessment, on_delete=models.CASCADE)
    ca_remediation_status = models.ForeignKey(Status, on_delete=models.PROTECT)

    finding_date = models.DateField()
    identifying_resource = models.ForeignKey(TKResources, on_delete=models.SET_NULL, null=True)
    finding_category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    finding_rca = models.TextField(verbose_name="Root Cause Analysis")

    ca_owner = models.CharField(max_length=255, verbose_name="Corrective Action Owner")
    ca_plan = models.TextField()
    ca_remediation_date = models.DateField(null=True, blank=True)


