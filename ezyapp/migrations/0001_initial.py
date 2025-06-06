# Generated by Django 5.2 on 2025-05-04 17:42

import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('phone_number', models.CharField(blank=True, max_length=15, null=True)),
                ('user_type', models.CharField(choices=[('poster', 'Job Poster'), ('helper', 'Helper')], max_length=10)),
                ('is_verified', models.BooleanField(default=False)),
                ('kyc_details', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='profile_pictures/')),
                ('otp', models.CharField(blank=True, max_length=6, null=True)),
                ('otp_created_at', models.DateTimeField(blank=True, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='HelperDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aadhaar_card', models.FileField(blank=True, null=True, upload_to='documents/aadhaar/')),
                ('driving_license', models.FileField(blank=True, null=True, upload_to='documents/driving_license/')),
                ('pan_card', models.FileField(blank=True, null=True, upload_to='documents/pan/')),
                ('selfie', models.ImageField(blank=True, null=True, upload_to='documents/selfie/')),
                ('status', models.CharField(choices=[('pending', 'Pending Verification'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=10)),
                ('rejection_reason', models.TextField(blank=True, null=True)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to=settings.AUTH_USER_MODEL)),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_documents', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('location_lat', models.DecimalField(decimal_places=7, max_digits=10)),
                ('location_long', models.DecimalField(decimal_places=7, max_digits=10)),
                ('location_address', models.CharField(max_length=255)),
                ('category', models.CharField(choices=[('pet', 'Pet Care'), ('home', 'Home Services'), ('outdoor', 'Outdoor Tasks'), ('delivery', 'Delivery'), ('other', 'Other')], max_length=20)),
                ('job_type', models.CharField(choices=[('fixed', 'Fixed Price'), ('hourly', 'Hourly Rate')], max_length=10)),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('hourly_rate', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('open', 'Open'), ('assigned', 'Assigned'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='open', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_jobs', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posted_jobs', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='JobApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('applied', 'Applied'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='applied', max_length=20)),
                ('message', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('helper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_applications', to=settings.AUTH_USER_MODEL)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='ezyapp.job')),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('comment', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews_received', to=settings.AUTH_USER_MODEL)),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews_given', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='wallet', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('credit', 'Credit'), ('debit', 'Debit')], max_length=10)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('reason', models.CharField(choices=[('job_payment', 'Job Payment'), ('withdrawal', 'Withdrawal'), ('deposit', 'Deposit'), ('refund', 'Refund'), ('other', 'Other')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('wallet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='ezyapp.wallet')),
            ],
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['user_type'], name='ezyapp_user_user_ty_d849bc_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['phone_number'], name='ezyapp_user_phone_n_82a52f_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['is_verified'], name='ezyapp_user_is_veri_82449c_idx'),
        ),
        migrations.AddIndex(
            model_name='helperdocument',
            index=models.Index(fields=['user'], name='ezyapp_help_user_id_db1d46_idx'),
        ),
        migrations.AddIndex(
            model_name='helperdocument',
            index=models.Index(fields=['status'], name='ezyapp_help_status_fa84bb_idx'),
        ),
        migrations.AddIndex(
            model_name='helperdocument',
            index=models.Index(fields=['verified_by'], name='ezyapp_help_verifie_943ada_idx'),
        ),
        migrations.AddIndex(
            model_name='helperdocument',
            index=models.Index(fields=['created_at'], name='ezyapp_help_created_2bfa35_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['user'], name='ezyapp_job_user_id_aeaa44_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['category'], name='ezyapp_job_categor_96f977_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['status'], name='ezyapp_job_status_de026d_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['assigned_to'], name='ezyapp_job_assigne_b4503f_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['created_at'], name='ezyapp_job_created_9406b7_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['start_time'], name='ezyapp_job_start_t_262fca_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['location_lat', 'location_long'], name='ezyapp_job_locatio_656f4f_idx'),
        ),
        migrations.AddIndex(
            model_name='jobapplication',
            index=models.Index(fields=['job'], name='ezyapp_joba_job_id_f391f3_idx'),
        ),
        migrations.AddIndex(
            model_name='jobapplication',
            index=models.Index(fields=['helper'], name='ezyapp_joba_helper__649c83_idx'),
        ),
        migrations.AddIndex(
            model_name='jobapplication',
            index=models.Index(fields=['status'], name='ezyapp_joba_status_d7b397_idx'),
        ),
        migrations.AddIndex(
            model_name='jobapplication',
            index=models.Index(fields=['created_at'], name='ezyapp_joba_created_fdb6fa_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='jobapplication',
            unique_together={('job', 'helper')},
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user'], name='ezyapp_noti_user_id_0c69fb_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['is_read'], name='ezyapp_noti_is_read_7be1d3_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['created_at'], name='ezyapp_noti_created_331c39_idx'),
        ),
        migrations.AddIndex(
            model_name='review',
            index=models.Index(fields=['reviewer'], name='ezyapp_revi_reviewe_f4dd94_idx'),
        ),
        migrations.AddIndex(
            model_name='review',
            index=models.Index(fields=['reviewed'], name='ezyapp_revi_reviewe_ea5554_idx'),
        ),
        migrations.AddIndex(
            model_name='review',
            index=models.Index(fields=['rating'], name='ezyapp_revi_rating_57ac20_idx'),
        ),
        migrations.AddIndex(
            model_name='review',
            index=models.Index(fields=['created_at'], name='ezyapp_revi_created_a260e4_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='review',
            unique_together={('reviewer', 'reviewed')},
        ),
        migrations.AddIndex(
            model_name='wallet',
            index=models.Index(fields=['user'], name='ezyapp_wall_user_id_d5cd9c_idx'),
        ),
        migrations.AddIndex(
            model_name='wallet',
            index=models.Index(fields=['balance'], name='ezyapp_wall_balance_60c0ac_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['wallet'], name='ezyapp_tran_wallet__6b6bec_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['type'], name='ezyapp_tran_type_5ac539_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['reason'], name='ezyapp_tran_reason_575dc6_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['created_at'], name='ezyapp_tran_created_44643b_idx'),
        ),
    ]
