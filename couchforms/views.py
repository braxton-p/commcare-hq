from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from couchforms.util import post_xform_to_couch
from django.http import HttpResponse, HttpResponseServerError
import logging
from couchforms.models import XFormInstance

@require_POST
@csrf_exempt
def post(request, callback=None, magic_property='xml_submission_file'):
    """
    XForms can get posted here.  They will be forwarded to couch.
    
    Just like play, if you specify a callback you get called, 
    otherwise you get a generic response.  Callbacks follow
    a different signature as play, only passing in the document
    (since we don't know what xform was being posted to)
    """
    # odk/javarosa preprocessing. These come in in different ways.
    attachments = {}
    if request.META['CONTENT_TYPE'].startswith('multipart/form-data'):
        #it's an standard form submission (eg ODK)
        #this does an assumption that ODK submissions submit using the form parameter xml_submission_file
        #todo: this should be made more flexibly to handle differeing params for xform submission
        instance = request.FILES[magic_property].read()
        for key, item in request.FILES.items():
            if key != magic_property:
                attachments[magic_property] = item

    else:
        #else, this is a raw post via a j2me client of xml (or touchforms)
        #todo, multipart raw submissions need further parsing capacity.
        instance = request.raw_post_data

    try:
        doc = post_xform_to_couch(instance, attachments=attachments)
        if callback:
            return callback(doc)
        return HttpResponse("Thanks! Your new xform id is: %s" % doc["_id"], status=201)
    except Exception, e:
        logging.exception(e)
        return HttpResponseServerError("FAIL")

def download_form(request, instance_id):
    instance = XFormInstance.get(instance_id) 
    response = HttpResponse(mimetype='application/xml')
    response.write(instance.get_xml())
    # if we want it to download like a file put somethingl like this
    # HttpResponse(mimetype='application/vnd.ms-excel')
    # response['Content-Disposition'] = 'attachment; filename=%s.xml' % instance_id
    return response

def download_attachment(request, instance_id, attachment):
    instance = XFormInstance.get(instance_id)
    attach = instance._attachments[attachment]
    response = HttpResponse(mimetype=attach["content_type"])
    response.write(instance.fetch_attachment(attachment))
    return response