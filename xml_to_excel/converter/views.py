import os
import tempfile
import xml.etree.ElementTree as ET
import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadFileForm

def get_text(element):
    return element.text if element is not None else None

def xml_to_dict(element):
    data_dict = {}
    for child in element:
        if len(child) > 0:
            data_dict[child.tag] = xml_to_dict(child)
        else:
            data_dict[child.tag] = get_text(child)
    return data_dict

def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f'{parent_key}{sep}{k}' if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def process_xml(file):
    tree = ET.parse(file)
    root = tree.getroot()

    general_segment_data = []
    bol_segment_data = []

    # Extract General Segment data
    general_segment = root.find('General_segment')
    if general_segment:
        general_segment_data.append(flatten_dict(xml_to_dict(general_segment)))

    # Extract Bol Segment data
    for bol_segment in root.findall('Bol_segment'):
        bol_dict = flatten_dict(xml_to_dict(bol_segment))
        
        # Extract ctn segments within bol_segment
        ctn_segments = bol_segment.findall('ctn_segment')
        if ctn_segments:
            for ctn_segment in ctn_segments:
                ctn_dict = flatten_dict(xml_to_dict(ctn_segment))
                combined_dict = {**bol_dict, **ctn_dict}
                bol_segment_data.append(combined_dict)
        else:
            bol_segment_data.append(bol_dict)

    df_general = pd.DataFrame(general_segment_data)
    df_bol = pd.DataFrame(bol_segment_data)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        with pd.ExcelWriter(tmp.name) as writer:
            df_general.to_excel(writer, sheet_name='General Segment', index=False)
            df_bol.to_excel(writer, sheet_name='Bol Segment with Ctn', index=False)
        tmp_path = tmp.name

    return tmp_path

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            tmp_path = process_xml(file)

            with open(tmp_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename=output.xlsx'
            os.remove(tmp_path)
            return response
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            output_file = process_xml(file)
            response = HttpResponse(open(output_file, 'rb').read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=output.xlsx'
            os.remove(output_file)  # Clean up the temporary file
            return response
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})
