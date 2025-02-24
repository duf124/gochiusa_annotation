各ファイル/フォルダの説明は以下の通り：

app.py: 
アノテーションサイトを立ちあげる実行ファイル。PowerShellでpython app.py、またはターミナルでpython3 app.pyと入力して実行するとローカル上にサイトが立つので、ログに表示されるIPアドレスのサイトにアクセスする。

extract_frames.py: 
各コマ画像を作成する実行ファイル。../dataset/FUZ_newを参照しているので、これらのファイルの上の階層にdatasetという名前のフォルダを準備しておき、その直下にFUZ_newという名前のフォルダを準備しておく。つまり、このプロジェクト内のファイルが入ったフォルダをgochiusa_annotationとすると、gochiusa_annotationとdatasetは同じフォルダ内に存在している必要がある。

frames: 
各コマ画像の入ったフォルダ。extract_framesが良い感じにやってくれるので特に気にしなくてよい。

web_data_annotator: 
サーバーサイドのコードやOCR結果をまとめたcsvを入れておくフォルダ。

web_data_annotator/templates: 
base.HTMLを入れておくフォルダ。

web_data_annotator/static: 
jsフォルダとcssフォルダを入れておくフォルダ。

web_data_annotator/static/js: 
scripts.jsを入れておくフォルダ。

web_data_annotator/static/css: 
styles.cssを入れておくフォルダ。

web_data_annotator/gochiusa_annotation.csv: 
OCR結果をまとめたcsv。indexとcolumnの参考用で実際のデータは入れていないものを上げている。
