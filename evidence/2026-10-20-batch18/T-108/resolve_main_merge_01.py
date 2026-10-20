"""Resolve only the reviewed 93fe03dcd / 12190c32f merge conflicts."""
import re
from pathlib import Path
import sys


def resolve_text(name, text):
    blocks = list(re.finditer(r'^<<<<<<< (?:HEAD|ours)\n(.*?)^=======\n(.*?)^>>>>>>> main\n', text, re.M | re.S))
    assert len(blocks) == (1 if name == 'panes.ts' else 5), (name, len(blocks))

    def replace(match):
        ours, theirs = match.group(1), match.group(2)
        if name == 'panes.ts':
            assert ours == "import { questionHookBinding, questionFromHook, projectQuestions, nativeAnswerKeys, type QuestionBinding } from './questions.ts';\n"
            assert theirs == 'import { AsyncLocalStorage } from "node:async_hooks";\n'
            return theirs + ours
        if 'default:' in ours:
            assert "default: 'questions'" in ours and "default: 'flow'" in theirs
            return ours.replace("default: 'questions'", "default: 'questions-flow'").replace(
                "'sidebar', 'questions'", "'sidebar', 'questions', 'flow', 'questions-flow'")
        if 'const withQuestions' in ours:
            assert "['a2a:answer']" in ours and "['a2a:flow']" in theirs
            value = ours.replace("values.contract === 'questions'", "['questions', 'questions-flow'].includes(values.contract)")
            value = value.replace("['sidebar','questions']", "['sidebar','questions','flow','questions-flow']")
            value = "  const withFlow = withCreation && ['flow','questions-flow'].includes(values.contract);\n" + value
            value = value.replace("...(withSidebar ? sidebarHandlers : [])]", "...(withSidebar ? sidebarHandlers : []), ...(withFlow ? ['a2a:flow'] : [])]")
            value = value.replace("...(withQuestions ? ['answer'] : [])]", "...(withQuestions ? ['answer'] : []), ...(withFlow ? ['flow'] : [])]")
            return value
        if ours == "  if (['sidebar','questions'].includes(values.contract)) {\n":
            assert theirs == "  if (['sidebar', 'flow'].includes(values.contract)) {\n"
            return "  if (['sidebar','questions','flow','questions-flow'].includes(values.contract)) {\n"
        assert 'const withCreation' in ours and 'const withCreation' in theirs
        return ours.replace("'sidebar','questions'", "'sidebar','questions','flow','questions-flow'")

    text = re.sub(r'^<<<<<<< (?:HEAD|ours)\n(.*?)^=======\n(.*?)^>>>>>>> main\n', replace, text, flags=re.M | re.S)
    if name != 'panes.ts':
        assert text.count("if (values.contract === 'flow')") == 1
        text = text.replace("if (values.contract === 'flow')", 'if (withFlow)')
        text = text.replace("['sidebar', 'flow'].includes(values.contract)", "['sidebar','questions','flow','questions-flow'].includes(values.contract)")
        text = text.replace("values.contract === 'flow' ? 'explicit_21_handler_and_22_bridge_names'",
                            "values.contract === 'questions-flow' ? 'explicit_22_handler_and_23_bridge_names' : ['flow','questions'].includes(values.contract) ? 'explicit_21_handler_and_22_bridge_names'")
    assert not re.search(r'^(?:<<<<<<<|=======|>>>>>>>)', text, re.M), name
    return text


if __name__ == '__main__':
    root = Path(sys.argv[1]).resolve(strict=True)
    paths = [root / 'workbench/src/panes.ts', root / 'workbench/tests/test_t091_pane_ipc.mjs']
    # Validate both before writing either. Unexpected conflicts preserve the scene.
    resolved = [(path, resolve_text(path.name, path.read_text(encoding='utf-8'))) for path in paths]
    for path, text in resolved:
        path.write_text(text, encoding='utf-8')
