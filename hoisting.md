
**Koszt:** ~€4.35/mies (~19 PLN)

---

## 🌐 Domena i SSL

| Rejestr | Typ domeny | Cena/rok |
|---------|------------|----------|
| **Cloudflare** | `.com` / `.dev` | ~45-55 PLN |
| OVH | `.ovh` | ~10 PLN |
| Porkbun | `.dev` / `.app` | ~50-60 PLN |
| home.pl | `.pl` | ~50-70 PLN |

**SSL:** Darmowy przez Let's Encrypt lub Cloudflare

---

## 🤖 Koszty zewnętrznych API

| Usługa | Użycie | Koszt |
|--------|--------|-------|
| Google Gemini API | LLM dla feedbacku/sugestii | Darmowy tier: 60 req/min |
| Expo Push Notifications | Powiadomienia push | Darmowe |

---

## 📈 Szacowany koszt miesięczny (100 użytkowników)

| Pozycja | Koszt/mies. |
|---------|-------------|
| Hetzner CX22 | ~19 PLN |
| Domena (roczna ÷ 12) | ~4 PLN |
| Backup (opcjonalnie) | ~4 PLN |
| Google Gemini API | 0 PLN (free tier) |
| **RAZEM** | **~23-27 PLN** |

---

## 🔧 Skalowanie

### Dla 500-1000 użytkowników
- Upgrade do Hetzner CX32 (4 vCPU, 8GB) - ~38 PLN/mies

### Dla 1000+ użytkowników
- Rozdzielenie serwisów na osobne maszyny
- Load balancer
- Managed database (np. Hetzner Managed PostgreSQL)
- Szacowany koszt: ~100-200 PLN/mies

---

## 📋 Checklist przed wdrożeniem

- [ ] Kupić domenę (Cloudflare rekomendowane)
- [ ] Utworzyć VPS na Hetzner
- [ ] Skonfigurować DNS (A record → IP serwera)
- [ ] Zainstalować Docker + Docker Compose
- [ ] Skonfigurować SSL (Certbot / Cloudflare)
- [ ] Ustawić zmienne środowiskowe produkcyjne
- [ ] Skonfigurować backup bazy danych
- [ ] Ustawić monitoring (opcjonalnie: Uptime Kuma)