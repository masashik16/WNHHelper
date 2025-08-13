embed = discord.Embed(title="モデレーションに関して",
                      description=f"下記に記載のない内容は[モデレーター規則](https://drive.google.com/file/d/1-rAK7WfKomAfxg7f_KgQc3DTd9NUYgy2/view?usp=sharing)を参照")
embed.add_field(name="モデレーションの流れ",
                value="1. 証拠の保全"
                      "\n証拠画像は下記画像と同一の形式で1枚～4枚の範囲でSSを保存すること。"
                      "\n2. 対応"
                      "\nメッセージの削除等やニックネームの強制変更等の対応を行う"
                      "\n3. 警告の発行"
                      "\n詳細は後記「モデレーション基準」を参照すること",
                inline=False)
embed.add_field(name="証拠SSの複数添付",
                value="最大4枚まで添付できます。"
                      "\n2枚以上添付したい際はコマンド入力画面の「他」をクリックして証拠画像X（数字）をクリックすると追加できるようになります。",
                inline=False)
embed.add_field(name="証拠SSに関して",
                value="証拠SSに関しては、あくまで**当該ユーザーの違反部分および本サーバーにおける違反であることを確認できる部分の範囲内のみを撮影するもの**とし、前後投稿等の違反に至る経緯等を確認するためのSS等は別途保存の上記録スレッドに投稿すること。",
                inline=False)
embed.add_field(name="判断に迷ったら",
                value="<#1115262454990127146>で議論の上判断すること。",
                inline=False)
embed.add_field(name="コマンド",
                value="https://discord.com/channels/977773343396728872/1205893364436832256",
                inline=False)
embed.add_field(name="ユーザーID（uid）の取得方法",
                value="設定>詳細設定 から開発者モードをONにする"
                      "\nユーザーを右クリックして「ユーザーIDをコピー」を選択",
                inline=False)
