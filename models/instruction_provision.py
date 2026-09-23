import mongoengine as me
from src.models.psped.foreas import Foreas
from src.models.ota.instruction_act import InstructionAct
from src.models.apografi.organizational_unit import OrganizationalUnit as Monada


class RegulatedObjectOta(me.EmbeddedDocument):
  regulatedObjectType = me.StringField(required=True, choices=["organization", "organizationalUnit", "remit", "ota"])
  regulatedObjectId = me.ObjectIdField(required=True)

class InstructionProvisionSpecs(me.EmbeddedDocument):
  arthro = me.StringField()
  paragrafos = me.StringField()
  edafio = me.StringField()

  def validate(self, clean=True):
    super(InstructionProvisionSpecs, self).validate(clean)
    fields = [self.arthro, self.paragrafos, self.edafio]
    if not any(fields):
      raise me.ValidationError("Κάποιο πεδίο της Εγκύκλιας Οδηγίας πρέπει να συμπληρωθεί")

class InstructionPages(me.EmbeddedDocument):
  from_pages = me.IntField()
  to_pages = me.IntField()

class InstructionProvision(me.Document):
  meta = {
    "collection": "instruction_provisions",
    "db_alias": "psped",
    "indexes": [
      { 
        # "fields": [
        #   "regulatedObject.regulatedObjectType", "regulatedObject.regulatedObjectId", 
        #   "instructionAct", "instructionProvisionSpecs.arthro", "instructionProvisionSpecs.paragrafos", "instructionProvisionSpecs.edafio"
        # ], "unique": True, "name":"regulatedObject_instructionAct_instructionProvisionSpecs"
        "fields": [
          "regulatedObject.regulatedObjectType", 
          "regulatedObject.regulatedObjectId",
          "instructionPages.from_pages",
          "instructionPages.to_pages",
          "instructionAct", 
          # "instructionProvisionSpecs.arthro", "instructionProvisionSpecs.paragrafos", "instructionProvisionSpecs.edafio"
        ], "unique": True, "name":"regulatedObject_instructionAct_instructionPages" 
      }
    ],
  }

  regulatedObject = me.EmbeddedDocumentField(RegulatedObjectOta, required=True)
  instructionAct = me.ReferenceField(InstructionAct, required=True)
  # instructionProvisionSpecs = me.EmbeddedDocumentField(InstructionProvisionSpecs, required=True)
  instructionProvisionText = me.StringField(required=True)
  instructionPages = me.EmbeddedDocumentField(InstructionPages)

  def to_dict(self):
    return {
      "_id": str(self.id),
      "regulatedObject": self.regulatedObject.to_mongo() if self.regulatedObject else None,
      "instructionAct": self.instructionAct.to_dict() if hasattr(self.instructionAct, "to_dict") else {
        "_id": str(self.instructionAct.id),
        **self.instructionAct.to_mongo().to_dict()
      },
      # "instructionProvisionSpecs": self.instructionProvisionSpecs.to_mongo() if self.instructionProvisionSpecs else None,
      "instructionProvisionText": self.instructionProvisionText,
      "instructionPages": self.instructionPages.to_mongo() if self.instructionPages else None,  
    }

  # A static method that receives an array of new instruction provisions and saves them to the database
  @staticmethod
  def save_new_instruction_provisions(instruction_provisions, regulatedObject):
    instruction_provisions_docs = []
    for provision in instruction_provisions:
      instructionActKey = provision["instructionActKey"]
      instructionAct = InstructionAct.objects.get(instructionActKey=instructionActKey)
      # instructionProvisionSpecs = provision["instructionProvisionSpecs"]
      instructionProvisionText = provision["instructionProvisionText"]
      instructionPages = provision.get("instructionPages")
      instructionProvision = InstructionProvision(
        regulatedObject=regulatedObject,
        instructionAct=instructionAct,
        # instructionProvisionSpecs=instructionProvisionSpecs,
        instructionProvisionText=instructionProvisionText,
        instructionPages=instructionPages
      ).save()
      instruction_provisions_docs.append(instructionProvision)
    return instruction_provisions_docs

  @staticmethod
  def regulated_object(code, instructionProvisionType):
    if instructionProvisionType == "organization":
      foreas = Foreas.objects.get(code=code)
      return RegulatedObjectOta(regulatedObjectType=instructionProvisionType, regulatedObjectId=foreas.id)
    elif instructionProvisionType == "organizationalUnit":
      monada = Monada.objects.get(code=code)
      return RegulatedObjectOta(regulatedObjectType=instructionProvisionType, regulatedObjectId=monada.id)
    elif instructionProvisionType == "remit":
      return RegulatedObjectOta(regulatedObjectType=instructionProvisionType, regulatedObjectId=code)
    elif instructionProvisionType == "ota":
      return RegulatedObjectOta(regulatedObjectType=instructionProvisionType, regulatedObjectId=code)
    else:
      raise ValueError("Invalid instructionProvisionType")
