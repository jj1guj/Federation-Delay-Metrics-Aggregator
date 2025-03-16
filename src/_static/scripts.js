document.addEventListener('DOMContentLoaded', function () {
    const gallery = document.getElementById('imageGallery');
    const imageCards = Array.from(document.querySelectorAll('.image-card'));
    const searchBox = document.getElementById('searchBox');
    const sortButtons = document.querySelectorAll('.sort-btn');
    const imageCountSpan = document.getElementById('imageCount');
    const modal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    const modalInfo = document.getElementById('modalInfo');
    const closeModal = document.querySelector('.close-modal');

    // 最終更新をローカル時刻で表示 (#lastUpdated要素)
    const lastUpdatedEl = document.getElementById('lastUpdated');
    if (lastUpdatedEl) {
        const utcIso = lastUpdatedEl.dataset.utc;
        if (utcIso) {
            const dateObj = new Date(utcIso);
            const localTimeStr = dateObj.toLocaleString();
            lastUpdatedEl.textContent = `最終更新: ${localTimeStr}`;
        }
    }

    // .update-utc を含む要素のテキストをローカル時刻に置き換える
    const updateEls = document.querySelectorAll('.update-utc');
    updateEls.forEach(el => {
        const utcIso = el.getAttribute('data-utc');
        if (utcIso) {
            const localTimeStr = new Date(utcIso).toLocaleString();
            el.textContent = `更新: ${localTimeStr}`;
        }
    });

    // data-date(UTC) をユーザーのローカルタイムへ変換する関数
    function toLocalTimeString(utcIsoString) {
        const dateObj = new Date(utcIsoString);
        return dateObj.toLocaleString();
    }

    // 検索機能
    searchBox.addEventListener('input', function () {
        const searchTerm = this.value.toLowerCase();
        let visibleCount = 0;
        imageCards.forEach(card => {
            const hostname = card.dataset.hostname.toLowerCase();
            if (hostname.includes(searchTerm)) {
                card.classList.remove('hidden');
                visibleCount++;
            } else {
                card.classList.add('hidden');
            }
        });
        imageCountSpan.textContent = visibleCount;
    });

    // ソート機能 (UTC文字列で比較)
    sortButtons.forEach(button => {
        button.addEventListener('click', () => {
            sortButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            const sortMethod = button.dataset.sort;

            const visibleCards = imageCards.filter(card => !card.classList.contains('hidden'));
            switch (sortMethod) {
                case 'date-desc':
                    visibleCards.sort((a, b) => new Date(b.dataset.date) - new Date(a.dataset.date));
                    break;
                case 'date-asc':
                    visibleCards.sort((a, b) => new Date(a.dataset.date) - new Date(b.dataset.date));
                    break;
                case 'name-asc':
                    visibleCards.sort((a, b) => a.dataset.hostname.localeCompare(b.dataset.hostname));
                    break;
                case 'size-desc':
                    visibleCards.sort((a, b) => parseInt(b.dataset.size) - parseInt(a.dataset.size));
                    break;
            }
            visibleCards.forEach(card => gallery.appendChild(card));
        });
    });

    // 画像クリックでモーダル表示 (ローカル日時)
    imageCards.forEach(card => {
        card.addEventListener('click', () => {
            const imageUrl = card.dataset.url;
            const hostname = card.dataset.hostname;
            const size = (parseInt(card.dataset.size, 10) / 1024).toFixed(1);
            const localTime = toLocalTimeString(card.dataset.date);

            modalImage.src = imageUrl;
            modalInfo.innerHTML = `
                <p><strong>ホスト名:</strong> ${hostname}</p>
                <p><strong>サイズ:</strong> ${size} KB</p>
                <p><strong>更新日時:</strong> ${localTime}</p>
                <p><a href="${imageUrl}" target="_blank" style="color:white;">画像を新しいタブで開く</a></p>
            `;
            modal.style.display = 'block';
        });
    });

    // モーダルを閉じる
    closeModal.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // モーダル外クリックで閉じる
    window.addEventListener('click', e => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    // ESCキーでモーダルを閉じる
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && modal.style.display === 'block') {
            modal.style.display = 'none';
        }
    });
});
