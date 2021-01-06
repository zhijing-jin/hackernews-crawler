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


def check_time():
    from datetime import datetime
    timestamp = 1564624227
    datetime.fromtimestamp(timestamp)

def get_date_range(start_date, end_date):
    import datetime
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')

    def daterange(start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + datetime.timedelta(n)

    date_range = []
    for single_date in daterange(start_date, end_date):
        date = single_date.strftime("%Y-%m-%d")
        date_range.append(date)
    return date_range

def main():
    import os
    import json
    from efficiency.log import fwrite

    data = []
    dates = []
    dir = '/home/ubuntu/proj/1908_clickbait/hacknews'
    output_json = 'stories.json'
    output_zip = 'stories.zip'
    file_filter = lambda f: f.startswith('stories_') and f.endswith('.json')

    fm = FileManager(dir=dir, file_filter=file_filter)
    print(json.dumps(fm.files, indent=4))
    for file in fm.files:
        with open(file) as f: content = json.load(f)
        data.extend(content[1:])
        dates.extend(list(content[0].values())[0])
        # show_var(
        #     ["file", "len(content)", "len(data)", "list(content.keys())[:3]"])
    import pdb;
    pdb.set_trace()
    len(data), len(dates)
    min(dates), max(dates)
    date_range = get_date_range(min(dates), max(dates))
    set(date_range) - set(dates)

    uniq_data = set(tuple(a.items()) for a in data)
    data = [dict(i) for i in uniq_data]
    data = sorted(data, key=lambda x: x['date'] + x['title'])
    fwrite(json.dumps(data, indent=4), os.path.join(dir, output_json))

    cmd = 'cd {dir}; zip {output_zip} {output_json} \n' \
          ' ~/proj/tools/gdrive-linux-x64 upload {output_zip}'        \
        .format(dir=dir, output_json=output_json, output_zip=output_zip)
    print('[Info] Executing command:', cmd)
    os.system(cmd)


if __name__ == '__main__':
    main()
