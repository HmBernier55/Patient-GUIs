from pymodm import MongoModel, fields


class Patient(MongoModel):
    name = fields.CharField()
    med_rec = fields.IntegerField(primary_key=True)
    med_images = fields.ListField()  # list of image encoding JSON strings
    heart_rates = fields.ListField()  # list of integer heart rates
    ecg_images = fields.ListField()  # list of image encoding JSON strings
    timestamps = fields.ListField()  # list of datetime strings for HR
