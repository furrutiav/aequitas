import logging
from datetime import datetime

from fpdf import FPDF
from tabulate import tabulate

logging.getLogger(__name__)

# Authors: Pedro Saleiro <saleiro@uchicago.edu>
#          Rayid Ghani
#
# License: Copyright \xa9 2018. The University of Chicago. All Rights Reserved.


def get_group_value_report(group_value_df):
    """

    :param group_value_df:
    :return:
    """
    group_value_report = {}
    the_false_df = group_value_df.loc[(group_value_df['Unsupervised Fairness'] == False) | (
            group_value_df['Supervised Fairness'] == False)]
    for index, row in the_false_df.iterrows():
        report = ''
        metrics = []
        group = row['group_variable'] + ' = ' + row['group_value']
        text1 = group + ' does not have '
        report += text1
        text2 = ''
        if row['Unsupervised Fairness'] is False:
            text2 += 'Unsupervised Fairness '
            text3 = ''
            if row['Statistical Parity'] is False:
                text3 += '(no Statistical Parity'
                ref_val = 0.0
                ref_group_value = group_value_df.loc[(group_value_df['group_variable'] == row[
                    'group_variable']) & (group_value_df['group_value'] == row[
                    'ppr_ref_group_value'])]['ppr'].values[0]
                ppr_text = '{:.2f}% of the group is selected, compared to {:.2f} % of the ' \
                           'reference group '.format(row['ppr'] * 100, ref_group_value * 100) + \
                           row['group_variable'] + ' = ' + row['ppr_ref_group_value']
                metrics.append(ppr_text)
            if row['Impact Parity'] is False:
                if text3 == '':
                    text3 += '(no Impact Parity)'
                else:
                    text3 += ', no Impact Parity)'
                pprev_text = ''
            else:
                text3 += ')'
            text2 += text3
        if row['Supervised Fairness'] is False:
            if text2 != '':
                text2 += ' neither '
            text2 += 'Supervised Fairness '
            text3 = ''
            if row['TypeI Parity'] is False:
                text3 += '(no Type I Parity'
            if row['TypeII Parity'] is False:
                if text3 == '':
                    text3 += '(no Type II Parity)'
                else:
                    text3 += ', no Type II Parity)'
            else:
                text3 += ') '
            text2 += text3
        report += text2
        group_value_report[group] = [report, metrics]

    return group_value_report


def get_highlevel_report(group_attribute_df):
    cols = ['model_id', 'score_threshold', 'attribute_name']
    if 'Unsupervised Fairness' in group_attribute_df.columns:
        cols.append('Unsupervised Fairness')
    if 'Supervised Fairness' in group_attribute_df.columns:
        cols.append('Supervised Fairness')
    highlevel_report = tabulate(group_attribute_df[cols], headers='keys', tablefmt='pipe')
    return highlevel_report


def audit_report_markdown(group_value_df, group_attribute_df, overall_fairness, fair_measures, model_id=1, parameter='binary'):
    report = '# The Report \n \n ## Overview at the attribute level\n\n'

    mkdown_highlevel = get_highlevel_report(group_attribute_df)

    report += mkdown_highlevel
    return report


def audit_report_pdf(model_id, parameter, model_eval, configs, fair_results, fair_measures,
                 group_value_df):
    """

    :param model_id:
    :param parameter:
    :param attributes:
    :param model_eval:
    :param configs:
    :param fair_results:
    :param fair_measures:
    :param ref_groups_method:
    :param group_value_df:
    :return:
    """
    group_value_report = get_group_value_report(group_value_df)
    project_description = configs.project_description
    if project_description is None:
        project_description = {'title': ' ', 'goal': ' '}
    if project_description['title'] is None:
        project_description['title'] = ' '
    if project_description['goal'] is None:
        project_description['goal'] = ' '
    print('\n\n\n:::::: REPORT ::::::\n')
    print('Project Title: ', project_description['title'])
    print('Project Goal: ', project_description['goal'])
    print('Bias Results:', str(fair_results))
    pdf = PDF()
    pdf.set_margins(left=20, right=15, top=10)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font('Arial', '', 16)
    pdf.cell(0, 5, project_description['title'], 0, 1, 'C')
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 10, datetime.now().strftime("%Y-%m-%d"), 0, 1, 'C')
    pdf.multi_cell(0, 5, 'Project Goal: ' + project_description['goal'], 0, 1)
    pdf.ln(2)
    model_metric = 'Precision at top ' + parameter
    pdf.multi_cell(0, 5, 'Model Perfomance Metric: ' + model_metric, 0, 1)
    pdf.multi_cell(0, 5, 'Fairness Measures: ' + ', '.join(fair_measures), 0, 1)
    pdf.ln(2)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.multi_cell(0, 5, 'Model Audited: #' + str(model_id) + '\t Performance: ' + str(model_eval),
                   0, 1)
    pdf.set_font('Helvetica', '', 11)

    ref_groups = ''
    if configs.ref_groups_method == 'predefined':
        if configs.ref_groups:
            ref_groups = str(configs.ref_groups)
    elif configs.ref_groups_method == 'majority':
        ref_groups = ''
    elif configs.ref_groups_method == 'min_metric':
        ref_groups = ''
    else:
        logging.error('audit_report(): wrong reference group method!')
        exit(1)
    pdf.multi_cell(0, 5, 'Group attributes provided for auditing: ' + ', '.join(configs.attr_cols), 0, 1)
    pdf.multi_cell(0, 5, 'Reference groups used: ' + configs.ref_groups_method + ':   '
                                                                         '' + ref_groups, 0, 1)
    pdf.ln(4)
    results_text = 'aequitas has found that model #' + str(model_id) + ' is '
    if fair_results['Overall Fairness'] is True:
        is_fair = 'FAIR'
        pdf.set_text_color(0, 128, 0)
        pdf.cell(0, 5, results_text + is_fair + '.', 0, 1)
    else:
        is_fair = 'UNFAIR'
        pdf.image('utils/img/danger.png', x=20, w=7, h=7)
        pdf.cell(73, 5, results_text, 0, 0)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(255, 0, 0)
        pdf.cell(0, 5, is_fair + '.', 0, 1)
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        for key, value in sorted(group_value_report.items()):
            pdf.ln(2)
            pdf.multi_cell(0, 5, value[0], 0, 1)
            pdf.ln(2)
            pdf.set_x(40.0)
            pdf.multi_cell(0, 5, '\t' + ', '.join(value[1]), 0, 1)
            pdf.ln(4)
            pdf.set_x(20.0)

    datestr = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_filename = 'aequitas_report_' + str(model_id) + '_' + project_description['title'].replace(' ',
                                                                                            '_') + '_' + datestr
    pdf.output('output/' + report_filename + '.pdf', 'F')
    return None


class PDF(FPDF):
    def header(self):
        # Logo
        self.image('utils/img/aequitas_report_header.png', x=5, w=0, h=20)
        self.ln(10)
        # Arial bold 15
        self.set_font('Arial', 'B', 20)
        # Move to the right
        self.cell(80)
        # Title
        self.cell(30, 10, 'Bias and Fairness Audit Report', 0, 0, 'C')
        # Line break
        self.ln(10)

    # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'aequitas \xa9 2017. The University of Chicago. All Rights '
                         'Reserved.     '
                         '\t \t'
                         'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

# fpdf.cell(w, h = 0, txt = '', border = 0, ln = 0,
#          align = '', fill = False, link = '')