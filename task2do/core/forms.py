from datetime import timedelta, date

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re

from .models import Worker, Manager, Project, Task, STATUS_CHOICES
from django_select2.forms import Select2MultipleWidget


class UserRegistrationForm(forms.ModelForm):
    USER_TYPE_CHOICES = (
        ('manager', 'manager'),
        ('worker', 'worker'),
    )

    username = forms.CharField(label='username')
    password = forms.CharField(widget=forms.PasswordInput, label='password')
    email = forms.EmailField(label='email')
    first_name = forms.CharField(label='first name')
    last_name = forms.CharField(label='surname')
    birth_date = forms.DateField(
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        label='date of birth'
    )
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, label='user type')

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name', 'birth_date']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists. Please choose another one.")
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')
        password_errors = []
        if len(password) < 8:
            password_errors.append(ValidationError("Password must be at least 8 characters long."))
        if not re.search(r'\d', password):
            password_errors.append(ValidationError("Password must contain at least one number."))
        if not re.search(r'\D', password):
            password_errors.append(ValidationError("Password must contain at least one letter."))
        if not re.search(r'\W', password):
            password_errors.append(ValidationError("Password must contain at least one symbol."))
        if password_errors:
            raise ValidationError(password_errors)
        return password

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user_type = self.cleaned_data.get('user_type')
        if user_type == 'manager':
            if Manager.objects.filter(personal_data__user__email=email).exists():
                raise ValidationError("Email already exists for this user type. Please choose another one.")
        else:
            if Worker.objects.filter(personal_data__user__email=email).exists():
                raise ValidationError("Email already exists for this user type. Please choose another one.")
        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        return last_name

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date > date.today():
            raise ValidationError("Birth date cannot be in the future.")
        elif birth_date > date.today() - timedelta(days=6 * 365):
            raise ValidationError("You must be at least 6 years old to register.")
        elif birth_date < date.today() - timedelta(days=120 * 365):
            raise ValidationError("Birth date cannot be more than 120 years in the past.")
        return birth_date


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField()



class WorkerMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, worker):
        return f"{worker.personal_data.user.first_name} {worker.personal_data.user.last_name} - {worker.personal_data.user.username}"

class CreateProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'members', 'due_date']
        widgets = {
            'members': Select2MultipleWidget,
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        manager_id = kwargs.pop('manager_id')
        super(CreateProjectForm, self).__init__(*args, **kwargs)
        manager = Manager.objects.get(personal_data__user__id=manager_id)
        self.fields['members'] = WorkerMultipleChoiceField(
            queryset=Worker.objects.filter(managers__id=manager.id),
            widget=Select2MultipleWidget
        )



class TaskEditForm(forms.ModelForm):
    status = forms.ChoiceField(choices=[(CHOICE, choice) for (CHOICE, choice) in STATUS_CHOICES if CHOICE != 'CANCELED'])

    class Meta:
        model = Task
        fields = ['status', 'title', 'description', 'is_active']

    def __init__(self, *args, **kwargs):
        super(TaskEditForm, self).__init__(*args, **kwargs)
        if not self.instance.parent_task:
            self.fields['title'].disabled = True
            self.fields['description'].disabled = True
            self.fields['is_active'].disabled = True

class ManagerTaskEditForm(forms.ModelForm):
    status = forms.ChoiceField(choices=[(CHOICE, choice) for (CHOICE, choice) in STATUS_CHOICES])

    class Meta:
        model = Task
        fields = ['status', 'title', 'description', 'is_active']

    def __init__(self, *args, **kwargs):
        super(ManagerTaskEditForm, self).__init__(*args, **kwargs)
        if self.instance.parent_task:
            self.fields['title'].disabled = True
            self.fields['description'].disabled = True
            self.fields['is_active'].disabled = True

class SubtaskDivisionForm(forms.Form):
    num_subtasks = forms.IntegerField(min_value=1, max_value=10, label='Number of Subtasks')

class SubtaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status']

SubtaskFormSet = forms.formset_factory(SubtaskForm, extra=1)


class ProjectChangeForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'is_active', 'due_date']


from django import forms
from .models import Task, Worker

class WorkerChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, worker):
        return f"{worker.personal_data.user.first_name} {worker.personal_data.user.last_name} - {worker.personal_data.user.username}"

class TaskCreationForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'assigned_to', 'due_date', 'description']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop('project_id')
        super(TaskCreationForm, self).__init__(*args, **kwargs)
        self.fields['assigned_to'] = WorkerChoiceField(queryset=Worker.objects.filter(projects__id=project_id))


class WorkerMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, worker):
        return f"{worker.personal_data.user.username} - {worker.personal_data.user.first_name} {worker.personal_data.user.last_name}"


class WorkerMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, worker):
        return f"{worker.personal_data.user.first_name} {worker.personal_data.user.last_name} - {worker.personal_data.user.username}"

class EditProjectWorkersForm(forms.ModelForm):
    members = WorkerMultipleChoiceField(
        queryset=Worker.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': 'Select Workers'})
    )

    class Meta:
        model = Project
        fields = ['members']

    def __init__(self, *args, **kwargs):
        manager_id = kwargs.pop('manager_id', None)
        manager = Manager.objects.get(personal_data__user__id=manager_id)
        super(EditProjectWorkersForm, self).__init__(*args, **kwargs)
        self.fields['members'].queryset = Worker.objects.filter(managers__id=manager.id)

class NewRequestForm(forms.Form):
    REQUEST_TYPE_CHOICES = (
        ('project', 'Project'),
        ('association', 'Association'),
    )

    def __init__(self, *args, user_type=None, **kwargs):
        super(NewRequestForm, self).__init__(*args, **kwargs)
        if user_type == 'manager':
            self.fields['type'] = forms.ChoiceField(choices=[self.REQUEST_TYPE_CHOICES[1]], label='Request Type')
        else:
            self.fields['type'] = forms.ChoiceField(choices=self.REQUEST_TYPE_CHOICES, label='Request Type')


class NewAssociationRequestForm(forms.Form):
    username = forms.CharField(label='Username')

class NewProjectRequestForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']


from django import forms
from .models import Project, REQUEST_TYPE

class ProjectChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, project):
        return project.name

class NewProjectRequestForm(forms.Form):
    project = ProjectChoiceField(queryset=Project.objects.none())
    title = forms.CharField(max_length=100)
    description = forms.CharField(widget=forms.Textarea)
    request_type = forms.ChoiceField(choices=([(REQUEST, request) for (REQUEST, request) in REQUEST_TYPE if REQUEST != 'ASOC']))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(NewProjectRequestForm, self).__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(members__personal_data__user=user)