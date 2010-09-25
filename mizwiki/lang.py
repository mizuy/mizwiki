# -*- coding:utf-8 mode:Python -*-


def upload(maxsize,exts):
    return 'アップロードできる最大サイズは %s KB、拡張子は %s です。' % (maxsize,exts)

def conflict(base,last):
    return '''
あなたの編集中に誰かが更新しました。
Base Revision: %s、Lastmodified Revision: %s
''' % (base,last)
    return '''
someone committed some file while you were editting.
base revision does not match: your base is Revision %s, but Lastmodified Revision is %s. 
''' % (base,last)

merge_success  = 'マージに成功しました。内容を確認して、Saveして下さい。'
merge_conflict = 'マージに失敗しました。マークのある行を手動で編集し、衝突を解決し、Saveして下さい。'
merge_error    = 'マージエラー 管理者に報告してください。'

