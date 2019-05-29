# -*- coding: utf-8 -*-
# pylint: disable=unsubscriptable-object, too-many-locals
from __future__ import print_function
from os.path import dirname, join
from copy import copy
from collections import OrderedDict
import json

from bokeh.layouts import layout, widgetbox
import bokeh.models as bmd
from bokeh.models.widgets import PreText, Button
from bokeh.io import curdoc
from jsmol_bokeh_extension import JSMol
from import_db import get_cif_content_from_disk as get_cif_str
from import_db import get_rdf_dataframe_from_disk as get_rdf_df
from import_db import get_results_dataframes_from_disk as get_results_df
#from import_db import get_cif_content_from_os as get_cif_str
from detail.query import get_sqlite_data as get_data

html = bmd.Div(text=open(join(dirname(__file__), "description.html")).read(),
               width=800)

download_js = open(join(dirname(__file__), "static", "download.js")).read()

plot_info = PreText(text='', width=300, height=100)
plot_info_not_sampled = PreText(
    text='We did not perform molecular simulations for this structure.',
    width=300,
    height=100)

btn_download_table = Button(label="Download json", button_type="primary")
btn_download_cif = Button(label="Download cif", button_type="primary")

zeolites = [
    'MTT', 'GOO', 'AFT', 'SFN', 'TSC', 'PAU', 'UEI', 'EMT', 'SFS', 'MFI'
]

cofs = [
    '16411C2', '15030N2', '16083N2', '17030N2', '17040N2', '17163N3',
    '15072N2', '18091N2', '13030N2', '17120N2'
]

mofs = [
    'NOCKUM_clean_min', 'BENXUP_clean_min', 'PIHNUQ_clean_min',
    'RIVDEF_clean_min', 'TUDJIM_freeONLY_min', 'NUTQEZ_clean_min',
    'DIYTEM_freeONLY_min', 'YUJNIB_clean_min', 'IBICIH_clean_min',
    'XOJWID_charged_min'
]

famous_mofs = [
    "ZIF-8", "ZIF-4", "UMCM-1", "UIO-66", "SBMOF-1", "MIL-125", "Mg-MOF-74",
    "IRMOF-10", "IRMOF-1", "Cu-BTC"
]

allowed_names = mofs + famous_mofs + cofs + zeolites


def get_name_from_url():
    args = curdoc().session_context.request.arguments
    try:
        name = args.get('name')[0]
        if isinstance(name, bytes):
            name = name.decode()
    except (TypeError, KeyError):
        name = 'TSC'

    return name


def errorbar(fig,
             x,
             y,
             xerr=None,
             yerr=None,
             color='#d62728',
             point_kwargs={},
             error_kwargs={}):
    """https://stackoverflow.com/a/30538908"""
    fig.circle(x, y, color=color, **point_kwargs)

    if xerr is not None:
        x_err_x = []
        x_err_y = []
        for px, py, err in zip(x, y, xerr):
            x_err_x.append((px - err, px + err))
            x_err_y.append((py, py))
        fig.multi_line(x_err_x, x_err_y, color=color, **error_kwargs)

    if yerr is not None:
        y_err_x = []
        y_err_y = []
        for px, py, err in zip(x, y, yerr):
            y_err_x.append((px, px))
            y_err_y.append((py - err, py + err))
    fig.multi_line(y_err_x, y_err_y, color=color, **error_kwargs)


def table_widget(entry):
    from bokeh.models import ColumnDataSource
    from bokeh.models.widgets import DataTable, TableColumn

    entry_dict = copy(entry.__dict__)
    print(entry_dict.keys())
    # Note: iterate over old dict, not the copy that is changing
    for k, v in entry.__dict__.items():
        if k == 'id' or k == '_sa_instance_state':
            del entry_dict[k]

        # use _units keys to rename corresponding quantity
        if k[-6:] == '_units':
            prop = k[:-6]
            new_key = "{} [{}]".format(prop, entry_dict[k])
            del entry_dict[k]
            entry_dict[new_key] = entry_dict.pop(prop)

    # order entry dict
    entry_dict = OrderedDict([(k, entry_dict[k])
                              for k in sorted(list(entry_dict.keys()))])

    data = dict(
        labels=[str(k) for k in entry_dict],
        values=[str(v) for v in entry_dict.values()],
    )
    source = ColumnDataSource(data)

    columns = [
        TableColumn(field="labels", title="Properties"),
        TableColumn(field="values", title="Values"),
    ]
    data_table = DataTable(source=source,
                           columns=columns,
                           width=500,
                           height=570,
                           index_position=None,
                           fit_columns=False)

    json_str = json.dumps(entry_dict, indent=2)
    btn_download_table.callback = bmd.CustomJS(args=dict(
        string=json_str, filename=entry_dict['name'] + '.json'),
                                               code=download_js)

    return widgetbox(data_table)


def rdf_plot(name):
    from bokeh.plotting import figure
    df_rdf = get_rdf_df(name)
    p = figure(
        width=800,
        height=int(800 / 1.61803),
        x_axis_label='r / A',
        y_axis_label='g(r)',
        title='methane-framework radial distribution function',
        active_drag='box_zoom',
        output_backend='webgl',
    )
    p.line(
        df_rdf.distance,
        df_rdf.histogram,
        color='#d62728',
    )

    return p


def get_grids(name, df_tailcorrection, df_no_tailcorrection):
    from bokeh.plotting import figure
    from bokeh.layouts import gridplot
    golden_ratio = 1.61803
    golden_ratio_reci = 1 / golden_ratio

    data_no_tail_correction = df_no_tailcorrection[df_no_tailcorrection['name']
                                                   == name]
    data_tail_correction = df_tailcorrection[df_tailcorrection['name'] == name]

    plot_width = 400
    plot_height = int(plot_width * golden_ratio_reci)

    # Henry coefficient
    p0 = figure(
        plot_width=plot_width,
        plot_height=plot_height,
        x_axis_label='cutoff / A',
        y_axis_label='Henry coefficient / (mol / kg / Pa)',
        y_axis_type="log",
        title='without tail-corrections',
        active_drag='box_zoom',
        output_backend='webgl',
    )
    p0.title.align = 'center'
    p0.title.text_font_size = '10pt'

    y0 = errorbar(
        p0,
        data_no_tail_correction['cutoff'],
        data_no_tail_correction['henry_coefficient_widom_average'],
        yerr=data_no_tail_correction['henry_coefficient_widom_dev'].values)

    p1 = figure(
        plot_width=plot_width,
        plot_height=plot_height,
        x_range=p0.x_range,
        y_range=p0.y_range,
        x_axis_label='cutoff / A',
        y_axis_label='Henry coefficient / (mol / kg / Pa)',
        y_axis_type="log",
        title='with tail-corrections',
        active_drag='box_zoom',
        output_backend='webgl',
    )
    p1.title.align = 'center'
    p1.title.text_font_size = '10pt'

    y1 = errorbar(
        p1,
        data_tail_correction['cutoff'],
        data_tail_correction['henry_coefficient_widom_average'],
        yerr=data_tail_correction['henry_coefficient_widom_dev'].values)

    # Loading 5.8 bar
    p2 = figure(
        plot_width=plot_width,
        plot_height=plot_height,
        x_axis_label='cutoff / A',
        y_axis_label='loading at 5.8 bar / (molecules / UC)',
        x_range=p0.x_range,
        active_drag='box_zoom',
        output_backend='webgl',
    )
    y2 = errorbar(p2,
                  data_no_tail_correction['cutoff'],
                  data_no_tail_correction['loading_absolute_average_low_p'],
                  yerr=data_no_tail_correction['loading_absolute_dev_low_p'])

    p3 = figure(
        plot_width=plot_width,
        plot_height=plot_height,
        x_range=p2.x_range,
        y_range=p2.y_range,
        x_axis_label='cutoff / A',
        y_axis_label='loading at 5.8 bar / (molecules / UC)',
        active_drag='box_zoom',
        output_backend='webgl',
    )
    y3 = errorbar(p3,
                  data_tail_correction['cutoff'],
                  data_tail_correction['loading_absolute_average_low_p'],
                  yerr=data_tail_correction['loading_absolute_dev_low_p'])

    # Loading 35 bar
    p4 = figure(
        plot_width=plot_width,
        plot_height=plot_height,
        x_axis_label='cutoff / A',
        y_axis_label='loading at 35 bar / (molecules / UC)',
        x_range=p0.x_range,
        active_drag='box_zoom',
        output_backend='webgl',
    )
    y4 = errorbar(
        p4,
        data_no_tail_correction['cutoff'],
        data_no_tail_correction['loading_absolute_average_medium_p'],
        yerr=data_no_tail_correction['loading_absolute_dev_medium_p'])

    p5 = figure(
        plot_width=plot_width,
        plot_height=plot_height,
        x_range=p4.x_range,
        y_range=p4.y_range,
        x_axis_label='cutoff / A',
        y_axis_label='loading at 35 bar / (molecules / UC)',
        active_drag='box_zoom',
        output_backend='webgl',
    )
    y5 = errorbar(p5,
                  data_tail_correction['cutoff'],
                  data_tail_correction['loading_absolute_average_medium_p'],
                  yerr=data_tail_correction['loading_absolute_dev_medium_p'])

    # Loading 65 bar
    p6 = figure(
        plot_width=plot_width,
        plot_height=plot_height,
        x_axis_label='cutoff / A',
        y_axis_label='loading at 35 bar / (molecules / UC)',
        x_range=p0.x_range,
        active_drag='box_zoom',
        output_backend='webgl',
    )
    y6 = errorbar(p6,
                  data_no_tail_correction['cutoff'],
                  data_no_tail_correction['loading_absolute_average_high_p'],
                  yerr=data_no_tail_correction['loading_absolute_dev_high_p'])

    p7 = figure(
        plot_width=plot_width,
        plot_height=plot_height,
        x_range=p6.x_range,
        y_range=p6.y_range,
        x_axis_label='cutoff / A',
        y_axis_label='loading at 35 bar / (molecules / UC)',
        active_drag='box_zoom',
        output_backend='webgl',
    )
    y7 = errorbar(p7,
                  data_tail_correction['cutoff'],
                  data_tail_correction['loading_absolute_average_high_p'],
                  yerr=data_tail_correction['loading_absolute_dev_high_p'])

    # Deliverable capacity
    p8 = figure(
        plot_width=plot_width,
        plot_height=plot_height,
        x_range=p0.x_range,
        x_axis_label='cutoff / A',
        y_axis_label='deliverable capacity / (molec. / UC)',
        active_drag='box_zoom',
        output_backend='webgl',
    )
    y8 = errorbar(p8,
                  data_no_tail_correction['cutoff'],
                  data_no_tail_correction['loading_absolute_average_high_p'] -
                  data_no_tail_correction['loading_absolute_average_low_p'],
                  yerr=data_no_tail_correction['loading_absolute_dev_high_p'] +
                  data_no_tail_correction['loading_absolute_dev_low_p'])

    p9 = figure(
        plot_width=plot_width,
        plot_height=plot_height,
        x_range=p8.x_range,
        y_range=p8.y_range,
        x_axis_label='cutoff / A',
        y_axis_label='deliverable capacity  / (molec. / UC)',
        active_drag='box_zoom',
        output_backend='webgl',
    )
    y9 = errorbar(p9,
                  data_tail_correction['cutoff'],
                  data_tail_correction['loading_absolute_average_high_p'] -
                  data_tail_correction['loading_absolute_average_low_p'],
                  yerr=data_tail_correction['loading_absolute_dev_high_p'] +
                  data_tail_correction['loading_absolute_dev_low_p'])

    grid = gridplot([[p0, p1], [p2, p3], [p4, p5], [p6, p7], [p8, p9]],
                    plot_width=plot_width,
                    plot_height=plot_height)

    return grid


# Maybe add here a plot with the CH4-Framework RDF

sizing_mode = 'fixed'
cof_name = get_name_from_url()
entry = get_data(cof_name, plot_info)

if cof_name in allowed_names:
    cif_str = get_cif_str(entry.filename)
    info = dict(
        height="100%",
        width="100%",
        use="HTML5",
        # serverURL="https://chemapps.stolaf.edu/jmol/jsmol/php/jsmol.php",
        # j2sPath="https://chemapps.stolaf.edu/jmol/jsmol/j2s",
        # serverURL="https://www.materialscloud.org/discover/scripts/external/jsmol/php/jsmol.php",
        # j2sPath="https://www.materialscloud.org/discover/scripts/external/jsmol/j2s",
        serverURL="detail/static/jsmol/php/jsmol.php",
        j2sPath="detail/static/jsmol/j2s",
        script="""set antialiasDisplay ON;
load data "cifstring"
{}
end "cifstring"
""".format(cif_str)
        ## Note: Need PHP server for approach below to work
        #    script="""set antialiasDisplay ON;
        # load cif::{};
        # """.format(get_cif_url(entry.filename))
    )

    btn_download_cif.callback = bmd.CustomJS(args=dict(
        string=cif_str, filename=entry.filename),
                                             code=download_js)
    script_source = bmd.ColumnDataSource()

    applet = JSMol(
        width=600,
        height=600,
        script_source=script_source,
        info=info,
        js_url="detail/static/jsmol/JSmol.min.js",
    )

    df_tailcorrection, df_no_tailcorrection = get_results_df()

    l = layout([
        [
            [[applet], [btn_download_cif]],
            [[table_widget(entry)], [btn_download_table]],
        ],
        [
            get_grids(cof_name,
                      df_tailcorrection=df_tailcorrection,
                      df_no_tailcorrection=df_no_tailcorrection)
        ],
        [rdf_plot(cof_name)],
        [plot_info],
    ],
               sizing_mode=sizing_mode)

else:
    l = layout([
        [
            [[table_widget(entry)], [btn_download_table]],
        ],
        [plot_info_not_sampled],
    ],
               sizing_mode=sizing_mode)

# We add this as a tab
tab = bmd.Panel(child=l, title=cof_name)
tabs = bmd.widgets.Tabs(tabs=[tab])

# Put the tabs in the current document for display
curdoc(
).title = "Applicability of tail-corrections in the molecular simulations of porous materials"
curdoc().add_root(layout([html, tabs]))
