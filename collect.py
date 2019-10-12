from os.path import isdir, dirname, realpath, basename
from os import listdir, path
from efficiency.function import shell
from efficiency.log import show_var


class FileManager():

    def __init__(self, dir=dirname(realpath(__file__)),
                 file_filter=lambda f: True):
        files = self.recurse_files(dir, file_filter=file_filter)
        self.files = sorted(files)

    @staticmethod
    def recurse_files(folder, file_filter=lambda f: True):
        if isdir(folder):
            return [path.join(folder, f) for f in listdir(folder)
                    if file_filter(f)]
        return [folder]

    def rename_files(self, prefix='My_mp3_'):
        for f in self.files:
            dir = dirname(f)
            fname = basename(f)
            new_fname = prefix + fname
            new_f = path.join(dir, new_fname)
            cmd = 'mv "{f}" "{new_f}"'.format(f=f, new_f=new_f)
            show_var(['cmd'])
            shell(cmd)


def get_most_common_in_list(ls, most_common_n=1):
    from collections import Counter
    cnt = Counter(ls)
    return cnt.most_common(most_common_n)


def check():
    import json

    file = '/home/ubuntu/proj/1908_clickbait/bitly/bitly.json'
    with open(file) as f:
        data = json.load(f)
    show_var(['len(data)', 'list(data.items())[99]'])
    titles = []
    for item in data.values():
        titles.append(item['title'])

    get_most_common_in_list(titles, most_common_n=10)

    good_data = {k: v for k, v in data.items() if 'nytimes' in v['long_url']}
    show_var(['len(good_data)'])
    import pdb;
    pdb.set_trace()


def check_time():
    from datetime import datetime
    timestamp = 1564624227
    datetime.fromtimestamp(timestamp)


def main():
    import os
    import json
    from efficiency.log import fwrite

    data = []
    dir = '/home/ubuntu/proj/1908_clickbait/hacknews'
    output_json = 'stories.json'
    output_zip = 'stories.zip'
    file_filter = lambda f: f.startswith('stories_') and f.endswith('.json')

    fm = FileManager(dir=dir, file_filter=file_filter)
    print(json.dumps(fm.files, indent=4))
    for file in fm.files:
        with open(file) as f: content = json.load(f)
        data.extend(content[1:])
        # show_var(
        #     ["file", "len(content)", "len(data)", "list(content.keys())[:3]"])
    import pdb;
    pdb.set_trace()
    len(data)
    fwrite(json.dumps(data, indent=4), os.path.join(dir, output_json))
    
    cmd = 'zip {output_zip} {output_json} \n' \
          '~/proj/tools/gdrive-linux-x64 upload {output_zip}' \
        .format(output_json='stories.json', output_zip='stories.zip')
    shell(cmd)


if __name__ == '__main__':
    main()
