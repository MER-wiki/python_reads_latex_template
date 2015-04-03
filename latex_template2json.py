#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import json
import re
import glob
import pypandoc
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


def put_to_txt(location, question_json):
    year = question_json['year']
    term = question_json['term']
    course = question_json['course']
    statement = question_json['statement_wiki']
    hints = question_json['hints_wiki']
    sols = question_json['sols_wiki']

    with open(location, 'w') as f:
        f.write(course + ' ' + term + ' ' + str(year) + '\n\n\n')
        f.write('Statement:\n')
        f.write(statement)
        f.write('\n\n\n\n\n')

        for zahl, hint in enumerate(hints):
            f.write('Hint_%s:\n' % (zahl + 1))
            f.write(hint)
            f.write('\n\n\n\n\n')

        for zahl, sol in enumerate(sols):
            f.write('Solution_%s:\n' % (zahl + 1))
            f.write(sol)
            f.write('\n\n\n\n\n')
    f.close()


def get_question_name(question):
    matches = re.findall(
        r"^{(.{1,5})}{(.{0,5})}{(.{0,5})}{(.{1,5})}", question)
    if not 1 == len(matches):
        raise AssertionError(
            "Could not correctly identify question name\n%s" % question)
    first, second, third, points = matches[0]
    qname = "%s_%s_%s" % (first, second, third)
    return qname.strip("_"), points


def remove_comments(question):
    lines = question.split('\n')
    text = ''
    for line in lines:
        line = line.split(' %')[0]
        text = text + line
    return text


def get_hints(question):
    hints = []
    hints_list = question.split('\\begin{hint}')
    for hint in hints_list[1:]:
        hint = hint.split('\\end{hint}')[0]
        hint = hint[hint.find('}') + 1:]
        hint = hint.strip()
        hints.append(hint)
    return hints


def get_solutions(question):
    solutions = []
    solutions_list = question.split('\\begin{solution}')
    for sol in solutions_list[1:]:
        sol = sol.split('\\end{solution}')[0]
        sol = sol[sol.find('}') + 1:]
        sol = sol.strip()
        solutions.append(sol)
    return solutions


def preCleaning(text):
    text = text.replace(u'\xe2', "'")
    text = text.replace('\\figure', ' MISSING FIGURE HERE:')
    text = text.replace('{eqnarray', '{align')
    return text


def postCleaning(text):
    text = text.replace('{aligned}', '{align}')
    text = text.replace('</p>', '').replace('<p>', '')

    # Handle <span>: This should trigger a new line...
    text = text.replace('</span>', '').replace('<span>', '\n\n')
    # unless it only contains a single word
    text = re.sub(r"\n\n('''\w+''')", r'\1', text)

    # Add space before and after <math> and </math> if not present
    text = re.sub(r'(\w)(<math>)', r'\1 \2', text)
    text = re.sub(r'(</math>)(\w)', r'\1 \2', text)

    # Add space after triple ''' if not present
    text = re.sub(r"([^\n\s]''')(\w)", r'\1 \2', text)

    # Add space in X.Y
    text = re.sub(r"(\w)\.(\w)", r'\1. \2', text)

    # Move quotation marks outside of <math>
    text = text.replace("<math>``", '"<math>').replace('"</math>', '</math>"')
    return text


def latex2wiki(latex_text):
    wiki_text = pypandoc.convert(
        preCleaning(latex_text), 'mediawiki', format='latex')
    wiki_text = postCleaning(wiki_text)
    wiki_text = wiki_text.strip()
    return wiki_text


def grap_question_info(question, course, year, term, solver):
    question = remove_comments(question)
    question_name, points = get_question_name(question)

    statement_latex = question.split('\\begin{statement}')[1].split(
        '\\end{statement}')[0].strip()
    hints_latex = get_hints(question)
    answer_latex = question.split('\\begin{answer}')[1].split(
        '\\end{answer}')[0].strip()
    solutions_latex = get_solutions(question)

    statement_wiki = latex2wiki(statement_latex)
    hints_wiki = []
    for hint in hints_latex:
        hints_wiki.append(latex2wiki(hint))
    answer_wiki = latex2wiki(answer_latex)
    solutions_wiki = []
    for sol in solutions_latex:
        solutions_wiki.append(latex2wiki(sol))

    question_json = {"course": course,
                     'year': int(year),
                     'term': term,
                     'statement_latex': statement_latex,
                     'statement_wiki': statement_wiki,
                     'hints_latex': hints_latex,
                     'hints_wiki': hints_wiki,
                     'sols_latex': solutions_latex,
                     'sols_wiki': solutions_wiki,
                     'answer_latex': answer_latex,
                     'answer_wiki': answer_wiki,
                     'question_name': question_name,
                     'points': int(points),
                     'solver': solver
                     }

    return question_json


if __name__ == '__main__':
    all_files = glob.glob('latex-exams/*.tex')
    if not all_files:
        print("Please put all .tex files in the folder 'latex-exams'")
        sys.exit(1)

    if not os.path.exists('json_data'):
        os.makedirs('json_data')

    for solved_exam in all_files:
        text = open(solved_exam, 'rU').read()

        course = text.split('\\newcommand{\\course}{')[1].split('}')[0]
        year = text.split('\\newcommand{\\term}{')[1].split('}')[
            0].split(' ')[1]
        term = text.split('\\newcommand{\\term}{')[1].split('}')[
            0].split(' ')[0]
        solver = text.split('\\newcommand{\\solver}{')[1].split('}')[0]

        where_to_save = os.path.join(
            'json_data', course, "%s_%s" % (term, year))

        try:
            os.makedirs(where_to_save)
        except OSError:
            # folder exists already
            pass

        questions = text.split('\\begin{question}')[1:]

        for question in questions:
            question_json = grap_question_info(
                question, course, year, term, solver)
            question_name = question_json['question_name']

            location = os.path.join(
                where_to_save, "Question_%s.json" % question_name)
            json.dump(
                question_json, open(location, "w"), indent=4, sort_keys=True)

            location = os.path.join(
                where_to_save, "Question_%s.txt" % question_name)
            put_to_txt(location, question_json)
