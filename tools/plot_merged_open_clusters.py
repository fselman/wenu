#!/usr/bin/env python3
"""Plot Dias/Hunt radii or member counts versus Hunt V10, with first-list symbols.

Dias has no independent V10. Identifier-matched Dias points share Hunt V10;
Dias-only entries remain in a separate missing-V10 panel, with no imputation.
Filled symbols use Dias values; hollow symbols use Hunt values. Member counts
are the separate published member_count columns, without division by two. This offline
curation tool changes no catalogue or chart defaults. No arguments shows help.
"""
import argparse
import hashlib
import json
from pathlib import Path
from catalogue_data_layout import CURATED
import sys
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
from astropy.table import Table

PRIORITY = ['messier','caldwell','sac_urban','rasc_finest_ngc','sac_best_ngc',
 'al_open_clusters','al_globular_clusters','herschel400_south','herschel400',
 'herschel2','sac_beyond_ngc','sac_asterisms','sac_red_stars','al_carbon_stars','al_dark_nebulae']
MARKERS = ['*','s','D','^','v','P','X','p','h','d','<','>','8','H','+']


def first_membership(table, priority):
    if not priority or len(priority)!=len(set(priority)) or any(p not in PRIORITY for p in priority):
        raise ValueError('Priority must contain distinct supported list names.')
    labels = np.full(len(table),'unlisted',dtype='U40')
    for name in reversed(priority):
        if 'in_'+name in table.colnames:
            labels[np.asarray(np.ma.filled(table['in_'+name],False),bool)] = name
    return labels


def number(row, column):
    if column not in row.colnames or np.ma.is_masked(row[column]): return np.nan
    return float(row[column])


def points(table, priority, dias_diameter='apparent_diameter_arcmin', hunt_diameter='apparent_diameter_arcmin', max_v10=None, max_ebv=None, *, x='radius'):
    if x not in ('radius','members'): raise ValueError('X must be radius or members.')
    for limit in (max_v10,max_ebv):
        if limit is not None and not np.isfinite(limit): raise ValueError('Cuts must be finite.')
    labels=first_membership(table,priority); rows=[]
    for i,row in enumerate(table):
        v10=number(row,'hunt_v10')
        for source,identifier,diameter in [('dias','dias_id',dias_diameter),('hunt','hunt_id',hunt_diameter)]:
            if identifier not in table.colnames or np.ma.is_masked(row[identifier]): continue
            radius=number(row,source+'_'+diameter)/2; ebv=number(row,source+'_reddening_e_bv')
            members=number(row,source+'_member_count')
            x_value=radius if x=='radius' else members
            reason=('invalid_'+x if not np.isfinite(x_value) or x_value<=0 else
              'missing_ebv' if max_ebv is not None and not np.isfinite(ebv) else
              'ebv_cut' if max_ebv is not None and ebv>max_ebv else
              'missing_v10' if not np.isfinite(v10) else
              'v10_cut' if max_v10 is not None and v10>=max_v10 else 'plotted')
            rows.append(dict(wenu_id=str(row['wenu_id']),source=source,radius_arcmin=radius,member_count=members,x_value=x_value,v10=v10,
              magnitude_source='hunt' if np.isfinite(v10) else '',first_list=labels[i],selection_status=reason))
    if not rows: raise ValueError('No Dias/Hunt source rows.')
    return Table(rows=rows)


def plot(point_table, priority, path, x='radius'):
    fig,(ax,missing)=plt.subplots(2,1,figsize=(11,8),sharex=True,
        gridspec_kw={'height_ratios':[5,1]},layout='constrained')
    styles={name:(MARKERS[PRIORITY.index(name)],plt.get_cmap('tab20')((2*PRIORITY.index(name))%20)) for name in priority}
    styles['unlisted']=('o','#999999'); legend=[]
    for category in ['unlisted']+list(reversed(priority)):
        marker,color=styles[category]; present=False
        for source in ['dias','hunt']:
            subset=point_table[(point_table['first_list']==category)&(point_table['source']==source)]
            good=subset['selection_status']=='plotted'; absent=subset['selection_status']=='missing_v10'
            for panel,mask,y in [(ax,good,subset['v10'][good]),(missing,absent,np.full(np.count_nonzero(absent),0 if source=='dias' else 1))]:
                if not np.any(mask): continue
                present=True
                panel.scatter(subset['x_value'][mask],y,marker=marker,
                  s=55 if category!='unlisted' else 12,linewidths=.8,
                  facecolors=color if source=='dias' else 'none',edgecolors=color,
                  alpha=.8 if category!='unlisted' else .35)
        if present: legend.append(Line2D([],[],marker=marker,color=color,linestyle='',label=category))
    ax.invert_yaxis(); ax.set_xscale('log'); ax.set_ylabel('Hunt-derived V10 (mag)')
    ax.set_title('Dias and Hunt '+('radii' if x=='radius' else 'member counts')+': first matching observing list')
    ax.grid(alpha=.2); missing.grid(axis='x',alpha=.2)
    missing.set_yticks([0,1],['Dias','Hunt']); missing.set_ylim(-.7,1.7)
    missing.set_ylabel('No V10')
    missing.set_xlabel(('Published angular radius (arcmin)' if x=='radius' else 'Published member count')+
        '\nFilled: Dias. Hollow: Hunt. Matched Dias points share Hunt V10.')
    ax.legend(handles=list(reversed(legend)),loc='upper left',bbox_to_anchor=(1.01,1),fontsize=8)
    fig.savefig(path,dpi=180); plt.close(fig)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog='Default priority: '+','.join(PRIORITY)+'\nPriority is configurable observing preference, not scientific rank.\n'
      'Usage: python tools/plot_merged_open_clusters.py --catalogue /path/wenu_open_clusters_v2.ecsv --output-directory /path/plots --name wenu_radius_v10_v1\n'
      'Use --x radius (default) or --x members (source-specific published member_count).\n'
      'Both X-axis choices require positive values and use a logarithmic scale; invalid values are logged.\n'
      'Optional --max-v10 11 (strict); --max-ebv 3 (source-specific). Exclusions are exported.')
    parser.add_argument('--catalogue',type=Path,default=CURATED/'open_star_clusters.ecsv',help='Trial output ECSV, or default active accepted catalogue under curated_catalogs/open_clusters.')
    parser.add_argument('--output-directory',type=Path,required=True)
    parser.add_argument('--name',default='wenu_radius_v10_v1')
    parser.add_argument('--x',choices=['radius','members'],default='radius',help='X axis: half selected source diameter, or original source member_count.')
    parser.add_argument('--priority',default=','.join(PRIORITY),help='Comma-separated list names; first true flag selects the only symbol.')
    parser.add_argument('--dias-diameter-column',default='apparent_diameter_arcmin')
    parser.add_argument('--hunt-diameter-column',default='apparent_diameter_arcmin',help='Default radius r50; alternatives tidal_diameter_arcmin, total_diameter_arcmin.')
    parser.add_argument('--max-v10',type=float); parser.add_argument('--max-ebv',type=float)
    arguments=sys.argv[1:] if argv is None else list(argv)
    if not arguments: parser.print_help(); return 0
    args=parser.parse_args(arguments)
    if not args.name or Path(args.name).name!=args.name: raise ValueError('Name must be a filename prefix.')
    priority=args.priority.split(','); table=Table.read(args.catalogue,format='ascii.ecsv')
    x_columns = (['dias_'+args.dias_diameter_column,'hunt_'+args.hunt_diameter_column]
                 if args.x=='radius' else ['dias_member_count','hunt_member_count'])
    for column in ['wenu_id','hunt_v10']+x_columns:
        if column not in table.colnames: raise ValueError('Required column missing: '+column)
    point_table=points(table,priority,args.dias_diameter_column,args.hunt_diameter_column,args.max_v10,args.max_ebv,x=args.x)
    paths={suffix:args.output_directory/(args.name+suffix) for suffix in ['.png','.svg','.pdf','_points.csv','_summary.json']}
    if any(p.exists() for p in paths.values()): raise FileExistsError('Plot products exist; use a new version.')
    args.output_directory.mkdir(parents=True,exist_ok=True)
    for suffix in ['.png','.svg','.pdf']: plot(point_table,priority,paths[suffix],args.x)
    point_table.write(paths['_points.csv'],format='ascii.csv')
    summary=dict(input_sha256=hashlib.sha256(args.catalogue.read_bytes()).hexdigest(),priority=priority,
      x=args.x, x_columns=x_columns,
      dias_radius='half '+args.dias_diameter_column,hunt_radius='half '+args.hunt_diameter_column,
      member_policy='Separate original dias_member_count and hunt_member_count; no scaling or substitution of accepted members.',
      magnitude='Hunt V10 for Hunt and identifier-matched Dias; no independent Dias V10',
      max_v10=args.max_v10,max_ebv=args.max_ebv,
      unavailable_flags=[p for p in priority if 'in_'+p not in table.colnames or np.all(np.ma.getmaskarray(table['in_'+p]))],
      counts={source:{status:int(np.count_nonzero((point_table['source']==source)&(point_table['selection_status']==status)))
        for status in set(point_table['selection_status'])} for source in ['dias','hunt']})
    paths['_summary.json'].write_text(json.dumps(summary,indent=2)+'\n')
    for path in paths.values(): print(path)
    return 0


if __name__=='__main__': raise SystemExit(main())
