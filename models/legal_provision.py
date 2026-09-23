import mongoengine as me
from models.psped.foreas import Foreas
from models.psped.legal_act import LegalAct
from models.apografi.organizational_unit import OrganizationalUnit as Monada


class RegulatedObject(me.EmbeddedDocument):
    regulatedObjectType = me.StringField(required=True, choices=["organization", "organizationalUnit", "remit", "ota"])
    # regulatedObjectCode = me.StringField(required=True)
    regulatedObjectId = me.ObjectIdField(required=True)
    # regulatedObjectObjectId = me.StringField()


class Abolition(me.EmbeddedDocument):
    abolishingLegalProvisionCode = me.StringField(required=True)
    entryDate = me.DateTimeField(required=True)
    userCode = me.StringField(required=True)


class LegalProvisionSpecs(me.EmbeddedDocument):
    meros = me.StringField()
    kefalaio = me.StringField()
    arthro = me.StringField()
    paragrafos = me.StringField()
    periptosi = me.StringField()
    ypoperiptosi = me.StringField()
    stoixeio = me.StringField()
    ypostoixeio = me.StringField()
    # edafio = me.StringField()
    pararthma = me.StringField()

    def validate(self, clean=True):
        super(LegalProvisionSpecs, self).validate(clean)
        fields = [self.meros, self.kefalaio, self.arthro, self.paragrafos, self.periptosi, self.ypoperiptosi, self.stoixeio, self.ypostoixeio, self.pararthma]
        if not any(fields):
          raise me.ValidationError("Κάποιο πεδίο της Διάταξης πρέπει να συμπληρωθεί")


class LegalProvision(me.Document):
    meta = {
        "collection": "legal_provisions",
        "db_alias": "psped",
        "indexes": [
            { "fields": [
                "regulatedObject.regulatedObjectType", "regulatedObject.regulatedObjectId", 
                "legalAct",
                "legalProvisionSpecs.meros", "legalProvisionSpecs.arthro", "legalProvisionSpecs.paragrafos", "legalProvisionSpecs.periptosi","legalProvisionSpecs.ypoperiptosi"
            ], "unique": True, "name":"regulatedObject_legalAct_legalProvisionSpecs" }
        ],
        # From index I have removed legalProvisionSpecs.kefalaio
    }

    # regulatedObject = me.EmbeddedDocumentField(RegulatedObject, required=True, unique_with=["legalAct", "legalProvisionSpecs"])
    regulatedObject = me.EmbeddedDocumentField(RegulatedObject, required=True)
    legalAct = me.ReferenceField(LegalAct, required=True)
    legalProvisionSpecs = me.EmbeddedDocumentField(LegalProvisionSpecs, required=True)
    legalProvisionText = me.StringField(required=True)
    abolition = me.EmbeddedDocumentField(Abolition)

    def to_dict(self):
      return {
        "_id": str(self.id),
        "regulatedObject": self.regulatedObject.to_mongo() if self.regulatedObject else None,
        "legalAct": self.legalAct.to_dict() if hasattr(self.legalAct, "to_dict") else {
            "_id": str(self.legalAct.id),
            **self.legalAct.to_mongo().to_dict()
        },
        "legalProvisionSpecs": self.legalProvisionSpecs.to_mongo() if self.legalProvisionSpecs else None,
        "legalProvisionText": self.legalProvisionText,
        "abolition": self.abolition.to_mongo() if self.abolition else None
      }

    # A static method that receives an array of new legal provisions and saves them to the database
    @staticmethod
    def save_new_legal_provisions(legal_provisions, regulatedObject):
        legal_provisions_docs = []
        for provision in legal_provisions:
            legalActKey = provision["legalActKey"]
            legalAct = LegalAct.objects.get(legalActKey=legalActKey)
            legalProvisionSpecs = provision["legalProvisionSpecs"]
            legalProvisionText = provision["legalProvisionText"]
            legalProvision = LegalProvision(
                regulatedObject=regulatedObject,
                legalAct=legalAct,
                legalProvisionSpecs=legalProvisionSpecs,
                legalProvisionText=legalProvisionText,
            ).save()
            legal_provisions_docs.append(legalProvision)
        return legal_provisions_docs

    @staticmethod
    def regulated_object(code, legalProvisionType):
        if legalProvisionType == "organization":
            foreas = Foreas.objects.get(code=code)
            return RegulatedObject(regulatedObjectType=legalProvisionType, regulatedObjectId=foreas.id)
        elif legalProvisionType == "organizationalUnit":
            monada = Monada.objects.get(code=code)
            return RegulatedObject(regulatedObjectType=legalProvisionType, regulatedObjectId=monada.id)
        elif legalProvisionType == "remit":
            return RegulatedObject(regulatedObjectType=legalProvisionType, regulatedObjectId=code)
        elif legalProvisionType == "ota":
            return RegulatedObject(regulatedObjectType=legalProvisionType, regulatedObjectId=code)
        else:
            raise ValueError("Invalid legalProvisionType")
