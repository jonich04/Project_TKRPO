from datetime import date

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from server.models import Account, Profile, Hospital, MedicalInfo, MedicalTest, IND_STATES, Appointment, Message, Speciality, APPOINTMENT_TYPE, Symptom


def validate_username_available(username):
    """ validator that throws an error if the given username already exists."""

    if User.objects.filter(username__icontains=username).count():
        raise forms.ValidationError("This email is already registered")


def validate_username_exists(username):
    """ validator that throws an error if the given username doesn't exists."""

    if not User.objects.filter(username__icontains=username).count():
        raise forms.ValidationError("Этот адрес электронной почты не существует")


def validate_birthday(birthday):
    """ validator to check if date is realistic """
    if birthday.year < (date.today().year -200):
        raise forms.ValidationError("Пожалуйста, выберите более позднюю дату")
    elif birthday > date.today():
        raise forms.ValidationError("Пожалуйста, выберите более раннюю дату")


def setup_field(field, placeholder=None):
    """
    This configures the given field to play nice with the bootstrap theme. Additionally, you can add
    an additional argument to set a placeholder text on the field.
    """
    field.widget.attrs['class'] = 'form-control'
    if placeholder is not None:
        field.widget.attrs['placeholder'] = placeholder


class BasicForm(forms.Form):
    def disable_field(self, field):
        """
        marks field as disabled
        :param field: name of the field
        """
        self.fields[field].widget.attrs['disabled'] = ""

    def mark_error(self, field, description):
        """
        Marks the given field as errous. The given description is displayed when the form it generated
        :param field: name of the field
        :param description: The error description
        """
        self._errors[field] = self.error_class([description])
        del self.cleaned_data[field]

    def clear_errors(self):
        self._errors = {}


class LoginForm(BasicForm):
    email = forms.EmailField(max_length=50,validators=[validate_username_exists])
    setup_field(email,'Введите адрес электронной почты здесь')
    password = forms.CharField(max_length=50,widget=forms.PasswordInput())
    setup_field(password,'Введите пароль здесь')

    def clean(self):
        """
        This is to make sure the password is valid for the given email.
        """
        cleaned_data = super(LoginForm,self).clean()
        username = cleaned_data.get('email')
        password = cleaned_data.get('пароль')
        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                self.mark_error('пароль', 'Неправильный пароль')
        return cleaned_data


class AccountRegisterForm(BasicForm):
    firstname = forms.CharField(label='имя',max_length=50)
    setup_field(firstname,'Введите имя здесь')
    lastname = forms.CharField(label='фамилия', max_length=50)
    setup_field(lastname, 'Введите фамилию здесь')
    email = forms.EmailField(max_length=50, validators=[validate_username_available])
    setup_field(email, 'Введите адрес электронной почты здесь')
    # speciality = forms.CharField(label="Speciality", required=False)
    # setup_field(speciality,"Enter speciality")
    password_first = forms.CharField(label='Пароль', min_length=1, max_length=50, widget=forms.PasswordInput())
    setup_field(password_first, "Введите пароль здесь")
    password_second = forms.CharField(label='', min_length=1, max_length=50, widget=forms.PasswordInput())
    setup_field(password_second, "Введите пароль еще раз")

    def clean(self):
        """This is to make sure both passwords fields have the same values in them. If they don't mark
        them as erroneous."""
        cleaned_data = super(AccountRegisterForm, self).clean()
        password_first = cleaned_data.get('пароль 1')
        password_second = cleaned_data.get('пароль 2')
        if password_first and password_second and password_first!=password_second:
            self.mark_error('password_second','Пароли не совпадают')
        return cleaned_data


class PasswordForm(BasicForm):
    password_current = forms.CharField(label='Текущий', max_length=50, widget=forms.PasswordInput())
    setup_field(password_current, 'Введите здесь свой текущий пароль')
    password_first = forms.CharField(label='New', max_length=50, widget=forms.PasswordInput())
    setup_field(password_first, "Введите новый пароль здесь")
    password_second = forms.CharField(label='', max_length=50, widget=forms.PasswordInput())
    setup_field(password_second, "Введите новый пароль еще раз")

    def clean(self):
        """
        This is to make sure both passwords fields have the same values in them. If they don't, mark
        them as erroneous. Also check if the current and new passwords are they same. If they are, then
        mark them as erroneous (we want different passwords).
        """
        cleaned_data = super(PasswordForm, self).clean()
        password_current = cleaned_data.get('пароль_текущий')
        password_first = cleaned_data.get('пароль 1')
        password_second = cleaned_data.get('пароль 2')
        if password_second and password_first:
            if password_second!=password_first:
                self.mark_error('password_second','Пароли не совпадают')
            if password_current and password_current == password_first:
                self.mark_error('password_current','Ваши текущий и новый пароли должны быть разными')
        return cleaned_data


class ProfileForm(BasicForm):
    firstname = forms.CharField(label='имя', max_length=50)
    setup_field(firstname,'Введите имя здесь')
    lastname = forms.CharField(label='Фамилия', max_length=50)
    setup_field(lastname, 'Введите фамилию здесь')
    sex = forms.ChoiceField(required=False, choices=Profile.GENDER)
    setup_field(sex)
    birthday = forms.DateField(required=False, validators=[validate_birthday])
    setup_field(birthday, 'Введите день рождения в формате ГГГГ-ММ-ДД.')
    phone = forms.CharField(required=False, max_length=10)
    setup_field(phone, 'Введите номер телефона здесь')
    allergies = forms.CharField(required=False, max_length=250)
    setup_field(allergies, 'Введите здесь любую аллергию')
    prefHospital = forms.ModelChoiceField(label="Предпочитаемая больница", required=False, queryset=Hospital.objects.all())
    setup_field(prefHospital)
    primaryCareDoctor = forms.ModelChoiceField(label="Врач первичной медико-санитарной помощи", required=False,
                                               queryset=Account.objects.filter(role=Account.ACCOUNT_DOCTOR))
    setup_field(primaryCareDoctor)
    speciality = forms.ModelChoiceField(label="специальность", required=False, queryset=Speciality.objects.all())
    setup_field(speciality)

    def assign(self, profile):
        profile.firstname = self.cleaned_data['firstname']
        profile.lastname = self.cleaned_data['lastname']
        profile.sex = self.cleaned_data['sex']
        if self.cleaned_data['birthday'] is not None:
            profile.birthday = self.cleaned_data['birthday']
        profile.phone = self.cleaned_data['phone']
        profile.allergies = self.cleaned_data['allergies']
        profile.prefHospital = self.cleaned_data['prefHospital']
        profile.primaryCareDoctor = self.cleaned_data['primaryCareDoctor']
        profile.speciality = self.cleaned_data['speciality']


class AppointmentForm(BasicForm):
    description = forms.CharField(required=True, max_length=50)
    setup_field(description,'Введите описание здесь')
    symptom = forms.ModelChoiceField(queryset=Symptom.objects.all())
    setup_field(symptom)
    hospital = forms.ModelChoiceField(queryset=Hospital.objects.all())
    setup_field(hospital)
    doctor = forms.ModelChoiceField(queryset=Account.objects.filter(role=Account.ACCOUNT_DOCTOR))
    setup_field(doctor)
    patient = forms.ModelChoiceField(queryset=Account.objects.filter(role=Account.ACCOUNT_PATIENT))
    setup_field(patient)
    appointment_type = forms.ChoiceField(choices=APPOINTMENT_TYPE)
    setup_field(appointment_type)
    startTime = forms.DateTimeField(label="Время начала")
    setup_field(startTime, "Введите в формате ГГГГ-ММ-ДД ЧЧ:ММ.")
    endTime = forms.DateTimeField(label="Врея окончания")
    setup_field(endTime, "Введите в формате ГГГГ-ММ-ДД ЧЧ:ММ.") 

    def assign(self, appointment):
        appointment.description = self.cleaned_data['description']
        appointment.symptom = self.cleaned_data['symptom']
        appointment.hospital = self.cleaned_data['hospital']
        appointment.doctor = self.cleaned_data['doctor']
        appointment.patient = self.cleaned_data['patient']
        appointment.appointment_type = self.cleaned_data['appointment_type']
        appointment.startTime = self.cleaned_data['startTime']
        appointment.endTime = self.cleaned_data['endTime']

    def generate(self):
        return Appointment(
            doctor=self.cleaned_data['doctor'],
            patient=self.cleaned_data['patient'],
            description=self.cleaned_data['description'],
            symptom=self.cleaned_data['symptom'],
            hospital=self.cleaned_data['hospital'],
            appointment_type = self.cleaned_data['appointment_type'],
            startTime=self.cleaned_data['startTime'],
            endTime=self.cleaned_data['endTime']
        )
    """
    This is a validator that checks if the appointment is conflicting with any other already
    made appointments
    """
    def clean(self):
        cleaned_data = super(AppointmentForm, self).clean()
        startTime = cleaned_data.get('время начала')
        endTime = cleaned_data.get('время окончания')
        if startTime and endTime:
            if endTime<=startTime:
                self.mark_error('endTime', 'Время окончания встречи должно наступать после времени начала.')
        return cleaned_data


class SpecialityForm(BasicForm):
    name = forms.CharField(label='Название специальности',max_length=50)
    setup_field(name, 'Введите сюда название специальности')
    description = forms.CharField(label='Название описания')
    setup_field(description, 'Введите описание специальности здесь')


class SymptomForm(BasicForm):
    name = forms.CharField(label='Название симптома',max_length=50)
    setup_field(name, 'Введите здесь название симптома')
    description = forms.CharField(label='Описание симптома')
    setup_field(description, 'Введите описание симптома здесь')


class EmployeeRegistrationForm(BasicForm):
    firstname = forms.CharField(label='Имя', max_length=50)
    setup_field(firstname,'Введите имя здесь')
    lastname = forms.CharField(label='Last Name', max_length=50)
    setup_field(lastname, 'Введите фамилию здесь')
    email = forms.EmailField(max_length=50, validators=[validate_username_available])
    setup_field(email, 'Введите адрес электронной почты здесь')
    password_first = forms.CharField(label='Пароль', min_length=1, max_length=50, widget=forms.PasswordInput())
    setup_field(password_first, "Введите пароль здесь")
    password_second = forms.CharField(label='', min_length=1, max_length=50, widget=forms.PasswordInput())
    setup_field(password_second, "Введите пароль еще раз")
    employee = forms.ChoiceField(required=False, choices=Account.EMPLOYEE_TYPES)
    setup_field(employee)
    speciality = forms.ModelChoiceField(label="специальность", required=False, queryset=Speciality.objects.all())
    setup_field(speciality)

    def clean(self):
        """
        This is to make sure both passwords fields have the same values in them. If they don't mark
        them as errous.
        """
        cleaned_data = super(EmployeeRegistrationForm,self).clean()
        password_first = cleaned_data.get('пароль 1')
        password_second = cleaned_data.get('пароль 2')
        employee = cleaned_data.get('сотрудник')
        speciality = cleaned_data.get('специальность')
        if password_first and password_second and password_first!=password_second:
            self.mark_error('password_second', 'Пароли не совпадают')
        if int(employee)==20 and speciality is None:
            self.mark_error('speciality', 'Врач должен иметь специализацию')
        if int(employee)!=20 and speciality is not None:
            self.mark_error('speciality', 'Только врач может иметь специальность')
        return cleaned_data


class PrescriptionForm(BasicForm):
    patient = forms.ModelChoiceField(queryset=Account.objects.filter(role=Account.ACCOUNT_PATIENT))
    setup_field(patient)
    doctor = forms.ModelChoiceField(queryset=Account.objects.filter(role=Account.ACCOUNT_DOCTOR))
    setup_field(doctor)
    date = forms.DateField()
    setup_field(date)
    medication = forms.CharField(max_length=50)
    setup_field(medication,"Введите лекарство здесь")
    strength = forms.CharField(max_length=30)
    setup_field(strength,"Введите силу здесь")
    instruction = forms.CharField(max_length=200)
    setup_field(instruction,"Введите инструкцию здесь")
    refill = forms.IntegerField()
    setup_field(refill,"Введите количество пополнений")
    active = forms.BooleanField(required=False)
    setup_field(active, "Проверьте после завершения")

    def assign(self, prescription):
        prescription.patient = self.cleaned_data['patient']
        prescription.doctor = self.cleaned_data['doctor']
        prescription.date = self.cleaned_data['date']
        prescription.medication = self.cleaned_data['medication']
        prescription.strength = self.cleaned_data['strength']
        prescription.instruction = self.cleaned_data['instruction']
        prescription.refill = self.cleaned_data['refill']
        prescription.active = self.cleaned_data['active']


class HospitalForm(BasicForm):
    city = forms.CharField(max_length=50)
    setup_field(city,"Введите город больницы")
    zip = forms.CharField(max_length=50)
    setup_field(zip,"Введите пин-код больницы")
    state = forms.CharField(max_length=50)
    setup_field(state, "Выберите область больницы")
    address = forms.CharField(max_length=100)
    setup_field(address, "Выберите адрес больницы")
    name = forms.CharField(max_length=50)
    setup_field(name,"Введите название больницы")
    phone = forms.CharField(max_length=10)
    setup_field(phone, "Введите номер телефона больницы")


class MedTestForm(BasicForm):
    name = forms.CharField(max_length=50)
    setup_field(name)
    date = forms.DateField()
    setup_field(date)
    hospital = forms.ModelChoiceField(queryset=Hospital.objects.all())
    setup_field(hospital)
    description = forms.CharField(max_length=200)
    setup_field(description,"Введите описание здесь")
    doctor = forms.ModelChoiceField(queryset=Account.objects.filter(role=Account.ACCOUNT_DOCTOR))
    setup_field(doctor)
    patient = forms.ModelChoiceField(queryset=Account.objects.filter(role=Account.ACCOUNT_PATIENT))
    setup_field(patient)
    private = forms.BooleanField(required=False)
    setup_field(private)
    completed = forms.BooleanField(required=False)
    setup_field(completed)
    image1 = forms.FileField(label='Image 1', required=False)
    setup_field(image1)
    image2 = forms.FileField(label='Image 2', required=False)
    setup_field(image2)
    image3 = forms.FileField(label='Image 3', required=False)
    setup_field(image3)
    image4 = forms.FileField(label='Image 4', required=False)
    setup_field(image4)
    image5 = forms.FileField(label='Image 5', required=False)
    setup_field(image5)

    def assign(self,medtest):
        medtest.name = self.cleaned_data['name']
        medtest.date = self.cleaned_data['date']
        medtest.hospital = self.cleaned_data['hospital']
        medtest.description = self.cleaned_data['description']
        medtest.doctor = self.cleaned_data['doctor']
        medtest.patient = self.cleaned_data['patient']
        medtest.private = self.cleaned_data['private']
        medtest.completed = self.cleaned_data['completed']
        medtest.image1 = self.cleaned_data['image1']
        medtest.image2 = self.cleaned_data['image2']
        medtest.image3 = self.cleaned_data['image3']
        medtest.image4 = self.cleaned_data['image4']
        medtest.image5 = self.cleaned_data['image5']

    def generate(self):
        return MedicalTest(
            name = self.cleaned_data['name'],
            date = self.cleaned_data['date'],
            hospital = self.cleaned_data['hospital'],
            description = self.cleaned_data['description'],
            doctor = self.cleaned_data['doctor'],
            patient = self.cleaned_data['patient'],
            private = self.cleaned_data['private'],
            completed = self.cleaned_data['completed'],
            image1 = self.cleaned_data['image1'],
            image2 =self.cleaned_data['image2'],
            image3 =self.cleaned_data['image3'],
            image4 =self.cleaned_data['image4'],
            image5 = self.cleaned_data['image5'],
        )


class MedTestDisplayForm(BasicForm):
    name = forms.CharField(max_length=50)
    setup_field(name)
    date = forms.DateField()
    setup_field(date)
    hospital = forms.ModelChoiceField(queryset=Hospital.objects.all())
    setup_field(hospital)
    description = forms.CharField(max_length=200)
    setup_field(description, "Введите описание здесь")
    doctor = forms.ModelChoiceField(queryset=Account.objects.filter(role=20))
    setup_field(doctor)
    patient = forms.ModelChoiceField(queryset=Account.objects.filter(role=10))
    setup_field(patient)
    private = forms.BooleanField(required=False)
    setup_field(private)
    completed = forms.BooleanField(required=False)
    setup_field(completed)

    def assign(self,medtest):
        medtest.name = self.cleaned_data['name']
        medtest.date = self.cleaned_data['date']
        medtest.hospital = self.cleaned_data['hospital']
        medtest.description = self.cleaned_data['description']
        medtest.doctor = self.cleaned_data['doctor']
        medtest.patient = self.cleaned_data['patient']
        medtest.private = self.cleaned_data['private']
        medtest.completed = self.cleaned_data['completed']


class MedicalInfoForm(BasicForm):
    account = forms.ModelChoiceField(label="Пациент", queryset=Account.objects.filter(role=Account.ACCOUNT_PATIENT))
    setup_field(account)
    bloodType = forms.ChoiceField(label="Группа крови",choices=MedicalInfo.BLOOD, required=False)
    setup_field(bloodType)
    allergy = forms.CharField(max_length=100, required=False)
    setup_field(allergy, "Введите здесь аллергию")
    alzheimer = forms.BooleanField(required=False)
    setup_field(alzheimer)
    asthma = forms.BooleanField(required=False)
    setup_field(asthma)
    diabetes = forms.BooleanField(required=False)
    setup_field(diabetes)
    stroke = forms.BooleanField(required=False)
    setup_field(stroke)
    comments = forms.CharField(max_length=500, required=False)
    setup_field(comments, "Введите дополнительную информацию здесь")

    def assign(self,medicalInfo):
        medicalInfo.account = self.cleaned_data['account']
        medicalInfo.bloodType = self.cleaned_data['bloodType']
        medicalInfo.allergy = self.cleaned_data['allergy']
        medicalInfo.alzheimer = self.cleaned_data['alzheimer']
        medicalInfo.asthma = self.cleaned_data['asthma']
        medicalInfo.diabetes = self.cleaned_data['diabetes']
        medicalInfo.stroke = self.cleaned_data['stroke']
        medicalInfo.comments = self.cleaned_data['comments']


class MessageForm(BasicForm):
    target = forms.ModelChoiceField(queryset=Account.objects.all(), label="To")
    setup_field(target)
    header = forms.CharField(max_length=300)
    setup_field(header,"Заголовок сообщения")
    body = forms.CharField(max_length=1000)
    setup_field(body,"Тело сообщения")

    def generate(self, sender):
        return Message(
            target=self.cleaned_data['target'],
            sender=sender,
            header=self.cleaned_data['header'],
            body=self.cleaned_data['body'],
        )


class ImportForm(forms.Form):
    upload = forms.FileField(required=True, widget=forms.FileInput())


class ExportForm(forms.Form):
    CHOICES = (
        ('hospitals','Download all hospitals'),
        ('users','Download all users'),
    )
    export = forms.ChoiceField(required=True,widget=forms.RadioSelect, choices=CHOICES)


class StatisticsForm(BasicForm):
    startDate = forms.DateTimeField(required=True,label="Начало")
    setup_field(startDate,"Enter as YYYY-MM-DD HH-MM")
    endDate = forms.DateTimeField(required=True, label="Конец")
    setup_field(endDate, "Enter as YYYY-MM-DD HH-MM")

    def assign(self,statistics):
        statistics.startTime = self.cleaned_data['startDate']
        statistics.endTime = self.cleaned_data['endDate']