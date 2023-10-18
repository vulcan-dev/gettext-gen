from pathlib import Path
from shutil import which
from deepl import Translator
from dotenv import dotenv_values
import argparse
import subprocess

config = dotenv_values('.env')
translator: Translator

# A list of files `xgettext` will scan in order to generate the pot file. It scans for the prefix ('_' by default) and `gettext(...)`
# Use any amount of files you want.
files: list = [
    'example.c',
]

def check_requirements() -> bool:
    programs = ['xgettext', 'msgfmt', 'msginit', 'msgmerge']

    failed = False
    for program in programs:
        if which(program) is None:
            print(f'Missing {program}')
            failed = True

    return not failed

def auto_translate_file(path: str, locale: str) -> bool:
    print(f'Translating {locale}')
    to_translate: list = []
    # line, text

    msg_english: str = ''

    with open(path, 'r') as f:
        line_num: int = 0
        lines = f.readlines()

        for line in lines:
            line_num += 1

            if not line.strip():
                continue

            if line[:5] == 'msgid':
                msg_english: str = line[7:len(line)-2]
                continue

            if line[:6] == 'msgstr':
                msg: str = line[8:len(line)-2]
                if len(msg) != 0: continue
                if len(msg_english) == 0: continue

                to_translate.extend([line_num, msg_english])
                # print(f'[{line_num}] {msg_english}')

        if len(to_translate) == 0:
            return True

        if len(to_translate) % 2 != 0: # Should never happen.
            raise Exception('Invalid number of elements in \'to_translate\'')
        
        # use google-translate
        to_send: list = to_translate[1::2]

        # Dummy data
        # translations: list = [ # this is what we will get from translating.
        #     'libfolders',
        #     # 'steam path',
        #     # 'executable',
        #     # 'no dll',
        #     # 'aslr',
        #     # 'createprocess',
        #     # 'virtualalloc',
        #     # 'bad write',
        #     # 'loadlib',
        #     # 'remotethread'
        # ]

        translations = translator.translate_text(to_send, target_lang=locale)

        if len(to_send) != len(translations):
            print(f'Did not receive the same length of data as we sent: {len(to_send)} - {len(translations)}')
            return False
        
        for i, x in enumerate(to_translate):
            if type(x) == int:
                line_num = x - 1
            else:
                translate_id = i // 2
                translated_text = translations[translate_id]
                lines[line_num] = f'msgstr "{translated_text}"\n'

        with open(path, 'w') as f:
            f.writelines(lines)

    pass

def create_default_config():
    config_text: str = '''GENERATED_DIR=generated
LANGUAGES=en,de,ru
KEYWORD=_
LANGUAGE=C++
PACKAGE_NAME=Change Me
PACKAGE_VERSION=0.0.0
COPYRIGHT_HOLDER=Change Me
COMMENTS=
BUGS_ADDRESS=Change Me'''

    try:
        with open('.env', 'w') as f:
            f.write(config_text)
    except Exception as e:
        print(f'Could not create default config: {e}')

def main() -> None:
    global translator

    # parse arguments
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('-t', '--translate', default=False, action='store_true', help='Whether or not to auto-translate missing fields')
    parser.add_argument('-c', '--config', default=False, action='store_true', help='Creates default .env')
    args = parser.parse_args()

    if args.config:
        create_default_config()
        print('Default configuration created, please edit the .env file and re-run.')
        return

    # read .env
    config_languages = config.get('LANGUAGES')
    if not config_languages:
        print('Missing "LANGUAGES" from environment, exiting.')
        return
    
    config_languages = config_languages.split(',')
    config_keyword = config.get('KEYWORD') or '_'
    config_domain = config.get('DOMAIN') or 'messages'
    config_out_dir = config.get('GENERATED_DIR') or ''
    config_language = config.get('LANGUAGE')
    config_package_name = config.get('PACKAGE_NAME') or 'Change Me'
    config_package_version = config.get('PACKAGE_VERSION') or '0.0.0'
    config_copyright_holder = config.get('COPYRIGHT_HOLDER') or 'Change Me'
    config_comments = config.get('COMMENTS') or ''
    config_bugs_address = config.get('BUGS_ADDRESS') or 'email@email.com'

    print(f'''Configuration:
  Package: {config_package_name} {config_package_version}
  Language: {config_language}
  Copyright Holder: {config_copyright_holder}
  Languages: {config_languages}
  Domain: {config_domain}
  Keyword: {config_keyword}
          ''')

    ## Connect to DeepL
    deepl_key = config.get('DEEPL_KEY')
    if args.translate and deepl_key is not None and len(deepl_key) > 0:
        try:
            translator = Translator(deepl_key)
            usage = translator.get_usage()

            if usage.any_limit_reached:
                print(f'Unable to use DeepL, reached maximum of {usage.character.limit} characters')
                translator = None

            if usage.character.count is not None:
                print(f'Using DeepL, used {usage.character.count}/{usage.character.limit} characters')
            else:
                print(f'Using DeepL')
        except Exception as e:
            translator = None
            print(f'Unable to use DeepL: {e}')

    if not check_requirements():
        return

    # setup directories
    po_dir = f'locales/po'
    compiled_dir = f'{config_out_dir}/locales'
    Path(po_dir).mkdir(parents=True, exist_ok=True)
    Path(compiled_dir).mkdir(parents=True, exist_ok=True)

    # xgettext
    xgettext_args = ['xgettext']
    xgettext_args = xgettext_args + files + [
        f'--language={config_language}',
        f'-k{config_keyword}',
        f'--package-name={config_package_name}',
        f'--package-version={config_package_version}',
        f'--copyright-holder={config_copyright_holder}',
        f'--add-comments={config_comments}',
        f'--msgid-bugs-address={config_bugs_address}',
        f'--output=locales/{config_domain}.pot']
    if subprocess.run(xgettext_args).returncode != 0:
        return # error gets printed for us.

    # setup language dirs
    for lang in config_languages:
        Path(f'{po_dir}/{lang}').mkdir(exist_ok=True)
        po_file: str = f'{po_dir}/{lang}/{config_domain}.po'
        messages_po: str = f'locales/{config_domain}.pot'

        # create 'locales/po/xxx/messages.po' if it doesn't exist
        if not Path(po_file).exists():
            subprocess.run([
                'msginit',
                '-i', messages_po, # input file
                '-o', po_file,
                '-l', lang, # locale
            ], stderr=subprocess.DEVNULL)
            print(f'Generated {po_file}')

        # merge everything from 'messages.pot' into the po file
        subprocess.run([
            'msgmerge',
            '-o', po_file,
            po_file,
            messages_po
        ], stderr=subprocess.DEVNULL)

        # translate the file
        if args.translate and translator and lang != 'en':
            auto_translate_file(po_file, lang)

        # format the locales
        mo_file: str = f'{po_dir}/{lang}/{config_domain}.mo'
        subprocess.run([
            'msgfmt',
            '-o', mo_file,
            po_file
        ])

        print(f'Updated translation for locales/{lang}')

        # move compiled files into the compiled dir
        Path(f'{compiled_dir}/{lang}/LC_MESSAGES').mkdir(exist_ok=True, parents=True)
        Path(mo_file).replace(f'{compiled_dir}/{lang}/LC_MESSAGES/messages.mo')

    print('Updated all translations!')

if __name__ == '__main__':
    main()