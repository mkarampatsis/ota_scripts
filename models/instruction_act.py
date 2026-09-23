from bson import ObjectId
import mongoengine as me
from src.models.upload import FileUpload
import uuid
from datetime import datetime

def default_ada():
  return f"ΜΗ ΑΝΑΡΤΗΤΕΑ ΠΡΑΞΗ-{uuid.uuid4()}"

class InstructionAct(me.Document):
  meta = {
    "collection": "instruction_acts",
    "db_alias": "psped",
    "indexes": [
      {"fields": ["instructionActType","instructionActNumber","instructionActDate","ada"], "unique": True}
    ],
  }

  instructionActKey = me.StringField(unique=True)
  instructionActType = me.StringField(
    required=True,
    choices=[
      'Εγκύκλιος',
      'Έγγραφο ',
    ]
  )
  instructionActNumber = me.StringField(required=True)
  instructionActDate = me.StringField(required=True)
  instructionActDateISO = me.DateTimeField()
  ada = me.StringField(default=default_ada, unique=True)
  instructionActFile = me.ReferenceField(FileUpload, required=True)

  def create_key(self):
    return f"{self.instructionActType} {self.instructionActNumber}/{self.instructionActDate}"
        
  def save(self, *args, **kwargs):

     # Convert "YYYY-MM-DD" string → Python date object
    try:
      self.instructionActDateISO = datetime.strptime(self.instructionActDate, "%Y-%m-%d").date()
    except ValueError:
      raise ValueError("Η ημερομηνία πρέπει να είναι μορφής YYYY-MM-DD")
    
    instructionActKey = self.create_key()

    existingDoc = InstructionAct.objects(instructionActKey=instructionActKey).first()
    if existingDoc:
      raise ValueError(f"Υπάρχει ήδη εγκύκλιος οδηγία με κλειδί {instructionActKey}")

    self.instructionActKey = instructionActKey

    file = FileUpload.objects.get(id=ObjectId(self.instructionActFile.id))
    if not file:
      raise ValueError(f"Δεν βρέθηκε αρχείο με id {self.instructionActFile.file_id}")

    super(InstructionAct, self).save(*args, **kwargs)
