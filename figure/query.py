"""Querying the DB
"""
from bokeh.models.widgets import RangeSlider, CheckboxButtonGroup
from config import max_points
import pandas as pd
# pylint: disable=too-many-locals
data_empty = dict(x=[0], y=[0], uuid=['1234'], color=[0], name=['no data'])


def get_data_sqla(projections, sliders_dict, quantities, plot_info):
    """Query database using SQLAlchemy.
    
    Note: For efficiency, this uses the the sqlalchemy.sql interface which does
    not go via the (more convenient) ORM.
    """
    from import_db import automap_table, engine
    from sqlalchemy.sql import select, and_

    Table = automap_table(engine)

    selections = []
    for label in projections:
        selections.append(getattr(Table, label))

    filters = []
    for k, v in sliders_dict.items():
        if isinstance(v, RangeSlider):
            if not v.value == quantities[k]['range']:
                f = getattr(Table, k).between(v.value[0], v.value[1])
                filters.append(f)
        elif isinstance(v, CheckboxButtonGroup):
            if not len(v.active) == len(v.labels):
                f = getattr(Table, k).in_([v.tags[i] for i in v.active])
                filters.append(f)

    s = select(selections).where(and_(*filters))

    results = engine.connect().execute(s).fetchall()

    nresults = len(results)
    if not results:
        plot_info.text = "No matching structure found."
        return data_empty
    elif nresults > max_points:
        results = results[:max_points]
        plot_info.text = "{} frameworks found.\nPlotting {}...".format(
            nresults, max_points)
    else:
        plot_info.text = "{} frameworks found.\nPlotting {}...".format(
            nresults, nresults)

    # x,y position
    x, y, clrs, names, filenames = zip(*results)
    x = list(map(float, x))
    y = list(map(float, y))

    print(projections)
    if projections[2] == 'group':
        #clrs = map(lambda clr: bondtypes.index(clr), clrs)
        clrs = list(clrs)
        # df = pd.DataFrame({
        #     'x': x,
        #     'y': y,
        #     'filename': filenames,
        #     'name': names,
        #     'color': clrs
        # })
        #
        # my_own_order = ['COFs', 'MOFs', 'zeolites', 'sampled']
        # my_own_order_dict = {key: i for i, key in enumerate(my_own_order)}
        # inv_my_own_order_dict = {v: k for k, v in my_own_order_dict.items()}
        # df['color_mapped'] = df['color'].map(my_own_order_dict)
        # df.sort_values(by=['color_mapped'], inplace=True)
        # x = df['x'].astype(float).to_list()
        # y = df['y'].astype(float).to_list()
        # filenames = df['filename'].to_list()
        # clrs = df['color'].to_list()
        # names = df['name'].to_list()
    else:
        clrs = list(map(float, clrs))

    return dict(x=x, y=y, filename=filenames, color=clrs, name=names)


def get_data_aiida(projections, sliders_dict, quantities, plot_info):
    """Query the AiiDA database"""
    from aiida import load_dbenv, is_dbenv_loaded
    from aiida.backends import settings
    if not is_dbenv_loaded():
        load_dbenv(profile=settings.AIIDADB_PROFILE)
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.data.parameter import ParameterData

    filters = {}

    def add_range_filter(bounds, label):
        # a bit of cheating until this is resolved
        # https://github.com/aiidateam/aiida_core/issues/1389
        #filters['attributes.'+label] = {'>=':bounds[0]}
        filters['attributes.' + label] = {
            'and': [{
                '>=': bounds[0]
            }, {
                '<': bounds[1]
            }]
        }

    for k, v in sliders_dict.items():
        # Note: filtering is costly, avoid if possible
        if not v.value == quantities[k]['range']:
            add_range_filter(v.value, k)

    qb = QueryBuilder()
    qb.append(
        ParameterData,
        filters=filters,
        project=['attributes.' + p
                 for p in projections] + ['uuid', 'extras.cif_uuid'],
    )

    nresults = qb.count()
    if nresults == 0:
        plot_info.text = "No matching frameworks found."
        return data_empty

    plot_info.text = "{} frameworks found. Plotting...".format(nresults)

    # x,y position
    x, y, clrs, uuids, names, cif_uuids = zip(*qb.all())
    plot_info.text = "{} frameworks queried".format(nresults)
    x = map(float, x)
    y = map(float, y)
    cif_uuids = map(str, cif_uuids)
    uuids = map(str, uuids)

    if projections[2] == 'group':
        #clrs = map(lambda clr: bondtypes.index(clr), clrs)
        clrs = map(str, clrs)
    else:
        clrs = map(float, clrs)

    return dict(x=x, y=y, uuid=cif_uuids, color=clrs, name=names)
