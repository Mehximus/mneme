# Mneme kurulumu (adım adım)

Toplam süre: 10 dakika. Bilgisayar bilgisi gerekmez.

## 1. Obsidian'ı indir

Obsidian notlarını okumak ve düzenlemek için kullanılan ücretsiz bir uygulama.

1. https://obsidian.md adresine git, **Download** düğmesine bas.
2. İnen dosyayı aç ve kur.
3. Obsidian açılınca **Create new vault** (Yeni kasa oluştur) seç.
4. Kasaya bir ad ver (örneğin `Beynim`), konum olarak `Belgeler` klasörünü seç, **Create** de.

Bu klasör senin ikinci beynin olacak. Yerini unutma.

## 2. Yapay zeka aracını aç

Hangisini kullanıyorsan onu aç:

- **Antigravity:** File → Open Folder → 1. adımda oluşturduğun klasörü seç.
- **Claude Code:** Klasörde terminal aç ve `claude` yaz.
- **Codex:** Klasörü Codex ile aç.

## 3. Bu mesajı yapıştır

Sohbet kutusuna aynen yapıştır ve gönder:

> https://raw.githubusercontent.com/Mehximus/mneme/main/mneme.md adresini oku. Bu klasöre ikinci beynimi kur. Mevcut kurulum varsa notlarımı koruyarak güncelle. Gerekli indirme ve kurulum adımlarını sen yap. Sonunda örnek bir bilgiyi kaydedip yeni oturumda geri okuyarak birlikte doğrulayalım.

Gerisini yapay zeka yapar. Bilgisayarında Python yoksa onu da kendisi kurar.

## 4. İzin isteklerini onayla

Kurulum sırasında araç "bu klasöre güveniyor musun", "hook'ları çalıştırayım mı" gibi sorular sorabilir. **Evet / İzin ver** de. Bunlar hafızanın her sohbette otomatik yüklenmesi için gerekli.

## 5. Tanış

Kurulum bitince yapay zeka sana adını, ne iş yaptığını ve nasıl konuşulmasını istediğini sorar. Cevapla. Bunları bir kere söylersin, sonraki her sohbette hatırlar.

## Çalışıyor mu?

Yeni bir sohbet aç ve şunu yaz: **"beni tanıyor musun?"**

Adınla cevap verip son konuştuklarınızı söylüyorsa her şey tamam.

## Notlarım nerede?

Obsidian'da kasanı aç. Hafıza dosyaları `🔮 850-Companion` klasöründe:

| Dosya | İçinde ne var |
|---|---|
| `Core.md` | Sen kimsin, nasıl çalışmak istiyorsun |
| `Kurallar.md` | Yapay zekaya yaptığın düzeltmeler |
| `Last-Session.md` | Son sohbetlerde ne yapıldı |
| `Threads.md` | Devam eden işler |

Bunları elle de düzenleyebilirsin.

## Güncelleme

Kasa klasöründeki **Mneme Guncelle.cmd** dosyasına çift tıkla (Mac'te `Mneme Güncelle.command`). Ya da yapay zekaya "mneme'yi güncelle" yaz.

## Sorun olursa

Yapay zekaya **"mneme doktor çalıştır"** yaz. Neyin bozuk olduğunu bulup düzeltir.
