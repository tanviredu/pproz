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
        
        # Extract Trader_segment and Shipping_agent_code within bol_segment
        trader_segment = bol_segment.find('Trader_segment')
        if trader_segment:
            shipping_agent_code = trader_segment.find('Shipping_agent_code')
            if shipping_agent_code is not None:
                bol_dict['Shipping_agent_code'] = get_text(shipping_agent_code)
        
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
    data = pd.DataFrame(bol_segment_data)
    
    df = pd.DataFrame()
    df['BL Nbr']       = data['Bol_id_Bol_reference']
    df['BL Type']      = data['Bol_id_Bol_type_code']
    df['MBL']          = data['Bol_id_Master_bol_ref_number']
    df['POL']          = data['Load_unload_place_Port_of_origin_code']
    df['Carrier Code'] = data['Traders_segment_Carrier_Carrier_code']
    df['Carrier Name'] = data['Traders_segment_Carrier_Carrier_name']
    df['Carrier Address'] = data['Traders_segment_Carrier_Carrier_address']
    df['Exporter Name'] = data['Traders_segment_Exporter_Exporter_name']
    df['Exporter address'] = data['Traders_segment_Exporter_Exporter_address']
    df['Notify name'] = data['Traders_segment_Notify_Notify_name']
    df['Notify address'] = data['Traders_segment_Notify_Notify_address']
    df['Consignee name'] = data['Traders_segment_Consignee_Consignee_name']
    df['Consignee address'] = data['Traders_segment_Consignee_Consignee_address']
    df['Unit Nbr'] = data['ctn_segment_Ctn_reference']
    df['No.of Pkg'] = data['ctn_segment_Number_of_packages']
    df['Type Length'] = data['ctn_segment_Type_of_container']
    df['Frght Kind'] = data['ctn_segment_Status']
    df['Seal Nbr1'] = data['ctn_segment_Seal_number']
    df['Cargo Wt (kg)'] = data['ctn_segment_Gross_weight']
    df['Pkg Code'] = data['Goods_segment_Package_type_code']
    df['Commodity Original'] = data['Goods_segment_Goods_description']
    df['CBM'] = data['Goods_segment_Volume_in_cubic_meters']
    df['Vatable'] = data['Goods_segment_Remarks']
    df['Shipping Agent'] = data['Traders_segment_Shipping_Agent_Shipping_Agent_code']
    df['Shipping Agent Name'] = data['Traders_segment_Shipping_Agent_Shipping_Agent_name']
    df['Cmdty Code'] = data['ctn_segment_Commodity_code']
    df['IMDG'] = data['Bol_id_DG_status']
    df['IMDG Code'] = data['ctn_segment_IMCO']
    df['UN No'] = data['ctn_segment_UN']

    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        with pd.ExcelWriter(tmp.name) as writer:
            df_general.to_excel(writer, sheet_name='General Segment', index=False)
            df.to_excel(writer, sheet_name='Bol Segment with Ctn', index=False)
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
