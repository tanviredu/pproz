import os
import tempfile
import xml.etree.ElementTree as ET
import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadFileForm

def get_text(element):
    return element.text if element is not None else None

def process_xml(file):
    tree = ET.parse(file)
    root = tree.getroot()

    general_data = []
    bol_data = []

    general_segment = root.find('General_segment')
    general_segment_id = general_segment.find('General_segment_id')
    totals_segment = general_segment.find('Totals_segment')
    transport_info = general_segment.find('Transport_information')
    load_unload_place = general_segment.find('Load_unload_place')

    general_data.append({
        'Customs_office_code': get_text(general_segment_id.find('Customs_office_code')),
        'Voyage_number': get_text(general_segment_id.find('Voyage_number')),
        'Date_of_departure': get_text(general_segment_id.find('Date_of_departure')),
        'Date_of_arrival': get_text(general_segment_id.find('Date_of_arrival')),
        'Total_number_of_bols': get_text(totals_segment.find('Total_number_of_bols')),
        'Total_number_of_packages': get_text(totals_segment.find('Total_number_of_packages')),
        'Total_number_of_containers': get_text(totals_segment.find('Total_number_of_containers')),
        'Total_gross_mass': get_text(totals_segment.find('Total_gross_mass')),
        'Carrier_code': get_text(transport_info.find('Carrier/Carrier_code')),
        'Carrier_name': get_text(transport_info.find('Carrier/Carrier_name')),
        'Carrier_address': get_text(transport_info.find('Carrier/Carrier_address')),
        'Mode_of_transport_code': get_text(transport_info.find('Mode_of_transport_code')),
        'Identity_of_transporter': get_text(transport_info.find('Identity_of_transporter')),
        'Nationality_of_transporter_code': get_text(transport_info.find('Nationality_of_transporter_code')),
        'Registration_number_of_transport_code': get_text(transport_info.find('Registration_number_of_transport_code')),
        'Master_information': get_text(transport_info.find('Master_information')),
        'Place_of_departure_code': get_text(load_unload_place.find('Place_of_departure_code')),
        'Place_of_destination_code': get_text(load_unload_place.find('Place_of_destination_code'))
    })

    for bol_segment in root.findall('Bol_segment'):
        bol_id = bol_segment.find('Bol_id')
        load_unload_place = bol_segment.find('Load_unload_place')
        traders_segment = bol_segment.find('Traders_segment')
        goods_segment = bol_segment.find('Goods_segment')
        value_segment = bol_segment.find('Value_segment')

        bol_data.append({
            'Bol_reference': get_text(bol_id.find('Bol_reference')),
            'Line_number': get_text(bol_id.find('Line_number')),
            'Bol_nature': get_text(bol_id.find('Bol_nature')),
            'Bol_type_code': get_text(bol_id.find('Bol_type_code')),
            'Consolidated_Cargo': get_text(bol_segment.find('Consolidated_Cargo')),
            'Port_of_origin_code': get_text(load_unload_place.find('Port_of_origin_code')),
            'Place_of_unloading_code': get_text(load_unload_place.find('Place_of_unloading_code')),
            'Carrier_code': get_text(traders_segment.find('Carrier/Carrier_code')),
            'Carrier_name': get_text(traders_segment.find('Carrier/Carrier_name')),
            'Carrier_address': get_text(traders_segment.find('Carrier/Carrier_address')),
            'Shipping_Agent_code': get_text(traders_segment.find('Shipping_Agent/Shipping_Agent_code')),
            'Shipping_Agent_name': get_text(traders_segment.find('Shipping_Agent/Shipping_Agent_name')),
            'Exporter_name': get_text(traders_segment.find('Exporter/Exporter_name')),
            'Exporter_address': get_text(traders_segment.find('Exporter/Exporter_address')),
            'Notify_name': get_text(traders_segment.find('Notify/Notify_name')),
            'Notify_address': get_text(traders_segment.find('Notify/Notify_address')),
            'Consignee_code': get_text(traders_segment.find('Consignee/Consignee_code')),
            'Consignee_name': get_text(traders_segment.find('Consignee/Consignee_name')),
            'Consignee_address': get_text(traders_segment.find('Consignee/Consignee_address')),
            'Number_of_packages': get_text(goods_segment.find('Number_of_packages')),
            'Package_type_code': get_text(goods_segment.find('Package_type_code')),
            'Gross_mass': get_text(goods_segment.find('Gross_mass')),
            'Shipping_marks': get_text(goods_segment.find('Shipping_marks')),
            'Goods_description': get_text(goods_segment.find('Goods_description')),
            'Volume_in_cubic_meters': get_text(goods_segment.find('Volume_in_cubic_meters')),
            'Num_of_ctn_for_this_bol': get_text(goods_segment.find('Num_of_ctn_for_this_bol')),
            'Remarks': get_text(goods_segment.find('Remarks')),
            'Freight_value': get_text(value_segment.find('Freight_segment/Freight_value')),
            'Freight_currency': get_text(value_segment.find('Freight_segment/Freight_currency')),
            'Customs_value': get_text(value_segment.find('Customs_segment/Customs_value')),
            'Customs_currency': get_text(value_segment.find('Customs_segment/Customs_currency'))
        })

    df_general = pd.DataFrame(general_data)
    df_bol = pd.DataFrame(bol_data)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        with pd.ExcelWriter(tmp.name) as writer:
            df_general.to_excel(writer, sheet_name='General Segment', index=False)
            df_bol.to_excel(writer, sheet_name='BOL Segment', index=False)
        tmp_path = tmp.name

    return tmp_path

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
