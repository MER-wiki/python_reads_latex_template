import os
import json
import re
import glob
import pypandoc
import sys


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


def postCleaning(text):
    return text.replace('{aligned}', '{align}')


def latex2wiki(latex_text):
    wiki_text = pypandoc.convert(latex_text, 'mediawiki', format='latex')
    wiki_text = postCleaning(wiki_text)
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
        text = open(solved_exam, 'r').read()

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
