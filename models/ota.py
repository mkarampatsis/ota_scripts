import mongoengine as me
from datetime import datetime
from src.models.timestamp import TimeStampedModel
from src.config import MONGO_PSPED_DB
from src.models.ota.instruction_provision import InstructionProvision
from src.models.psped.legal_provision import LegalProvision

class COFOG(me.EmbeddedDocument):
  cofog1 = me.StringField()
  cofog1_name = me.StringField()
  cofog2 = me.StringField()
  cofog2_name = me.StringField()
  cofog3 = me.StringField()
  cofog3_name = me.StringField() 

class PublicPolicyAgency(me.EmbeddedDocument):
  organization = me.StringField(required=True)
  organizationCode = me.StringField(required=True)
  organizationType = me.StringField(required=True)
  status = me.StringField(required=True)
  subOrganizationOf = me.StringField(required=True)
  subOrganizationOfCode = me.StringField(required=True)

class Ota(TimeStampedModel):
  meta = {"collection": "ota", "db_alias": MONGO_PSPED_DB}

  remitText = me.StringField(required=True)
  remitCompetence = me.StringField(
    required=True,
    choices=[
      'Περιφέρειες',
      'Δήμοι',
      'Νησιωτικοί Δήμοι',
      'Ορεινοί Δήμοι',
      'Μητροπολιτικές Αρμοδιότητες'
    ]
  )
  remitType = me.StringField(
    required=True,
    choices=[
      'Επιτελική',
      'Εκτελεστική',
      'Υποστηρικτική',
      'Ελεγκτική',
      'Παρακολούθησης αποτελεσματικής πολιτικής και αξιολόγησης αποτελεσμάτων'
    ],
  )
  remitLocalOrGlobal = me.StringField(
    required=True,
    choices=[
      'Αυτοδιοικητική Αρμοδιότητα (Τοπική)',
      'Αρμοδιότητα που συνιστά αποστολή του κράτους (Κρατική)'
    ],
  )
  legalProvisionRefs = me.ListField(me.ReferenceField(LegalProvision))
  instructionProvisionRefs = me.ListField(me.ReferenceField(InstructionProvision))
  publicPolicyAgency = me.EmbeddedDocumentField(PublicPolicyAgency)
  cofog = me.EmbeddedDocumentField(COFOG)
  status = me.StringField(choices=["ΕΝΕΡΓΗ", "ΑΝΕΝΕΡΓΗ"], default="ΕΝΕΡΓΗ")
  finalized = me.BooleanField(default=False)
  elasticSync = me.BooleanField(default=False)

  def to_dict(self):
    
    def provision_to_dict_instruction(provision: InstructionProvision):
      if not provision:
          return None

      return {
        "_id": str(provision.id),
        "regulatedObject": provision.regulatedObject.to_mongo(),
        "instructionAct": (
            provision.instructionAct.to_mongo()
            if provision.instructionAct else None
        ),
        "instructionActKey" : provision.instructionAct.instructionActKey if provision.instructionAct else None,
        # "instructionProvisionSpecs": provision.instructionProvisionSpecs.to_mongo(),
        "instructionProvisionText": provision.instructionProvisionText,
        "instructionPages": provision.instructionPages.to_mongo(),
      }
    
    def provision_to_dict_legal(provision: LegalProvision):
      if not provision:
          return None
      
      return {
        "_id": str(provision.id),
        "regulatedObject": provision.regulatedObject.to_mongo(),
        "legalAct": (
            provision.legalAct.to_mongo()
            if provision.legalAct else None
        ),
        "legalActKey" : provision.legalAct.legalActKey if provision.legalAct else None,
        "legalProvisionSpecs": provision.legalProvisionSpecs.to_mongo(),
        "legalProvisionText": provision.legalProvisionText,
      }

    # Convert instructionProvisionRefs (ObjectIds) → actual docs
    legal_provisions = []
    for ref in self.legalProvisionRefs:
      provision = LegalProvision.objects(id=ref.id).first()
      if provision:
        legal_provisions.append(provision_to_dict_legal(provision))

    instruction_provisions = []
    for ref in self.instructionProvisionRefs:
      provision = InstructionProvision.objects(id=ref.id).first()
      if provision:
        instruction_provisions.append(provision_to_dict_instruction(provision))

    return {
      "_id": str(self.id),
      "remitText": self.remitText,
      "remitCompetence": self.remitCompetence,
      "remitType": self.remitType,
      "remitLocalOrGlobal": self.remitLocalOrGlobal,
      "legalProvisions": legal_provisions,
      "instructionProvisions": instruction_provisions,
      "publicPolicyAgency": self.publicPolicyAgency.to_mongo() if self.publicPolicyAgency else None,
      "cofog": self.cofog.to_mongo() if hasattr(self, 'cofog') else None,
      "status": self.status,
      "finalized": self.finalized,
      "elasticSync": self.elasticSync,
      "createdAt": self.createdAt,
      "updatedAt": self.updatedAt,
    }