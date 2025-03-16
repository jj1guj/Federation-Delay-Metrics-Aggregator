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

    // タッチ操作の状態を管理
    const touch = {
        startX: 0,
        startY: 0,
        endX: 0,
        endY: 0,
        startTime: 0,
        element: null,
        isScrolling: false
    };

    // 最終更新をローカル時刻で表示
    const lastUpdatedEl = document.getElementById('lastUpdated');
    if (lastUpdatedEl) {
        const utcIso = lastUpdatedEl.dataset.utc;
        if (utcIso) {
            const dateObj = new Date(utcIso);
            const localTimeStr = dateObj.toLocaleString();
            lastUpdatedEl.textContent = `最終更新: ${localTimeStr}`;
        }
    }

    // .update-utc を含む要素をローカル時刻に
    const updateEls = document.querySelectorAll('.update-utc');
    updateEls.forEach(el => {
        const utcIso = el.getAttribute('data-utc');
        if (utcIso) {
            const localTimeStr = new Date(utcIso).toLocaleString();
            el.textContent = `更新: ${localTimeStr}`;
        }
    });

    // 生成日時をローカルタイムに
    const generatedAtEl = document.getElementById('generatedAt');
    if (generatedAtEl) {
        const utcIso = generatedAtEl.dataset.utc;
        if (utcIso) {
            const localTimeStr = new Date(utcIso).toLocaleString();
            generatedAtEl.textContent = `生成日時: ${localTimeStr}`;
        }
    }

    // ローカル時間変換関数
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

    // ソート機能
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

    // モーダル表示関数
    function showModal(card) {
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
    }

    // モーダルを閉じる関数
    function hideModal() {
        modal.style.display = 'none';
    }

    // PCユーザー向けのクリックイベント (スマホではこれは発火しにくい)
    imageCards.forEach(card => {
        // PC用のクリックイベント (touchイベントは別処理)
        card.addEventListener('click', (e) => {
            // モバイルデバイスの場合は無視 (touchイベントが処理するため)
            if ('ontouchstart' in window) return;
            showModal(card);
        });
    });

    // =========== タッチイベントの処理（スクロールとタップを区別） ===========

    // スクロール検出用のタッチ開始イベント
    document.addEventListener('touchstart', (e) => {
        // モーダルが開いている場合は特別処理
        if (modal.style.display === 'block') {
            if (e.target === modal) {
                e.preventDefault();
            }
            return;
        }

        touch.startX = e.touches[0].clientX;
        touch.startY = e.touches[0].clientY;
        touch.startTime = Date.now();
        touch.element = e.target;
        touch.isScrolling = false;

        // スクロール開始から50ms後にスクロール判定
        setTimeout(() => {
            // 50ms以内に10px以上動いていたらスクロール開始と判断
            const currentY = window.scrollY;
            if (Math.abs(window.scrollY - currentY) > 5) {
                touch.isScrolling = true;
            }
        }, 50);
    }, { passive: true });

    // スクロール中のフラグを設定
    document.addEventListener('scroll', () => {
        touch.isScrolling = true;
    }, { passive: true });

    // タッチ終了時のイベント
    document.addEventListener('touchend', (e) => {
        // モーダルが表示中の場合
        if (modal.style.display === 'block') {
            if (e.target === modal) {
                hideModal();
                e.preventDefault();
            }
            return;
        }

        // スクロール中だった場合はタップとして処理しない
        if (touch.isScrolling) {
            return;
        }

        touch.endX = e.changedTouches[0].clientX;
        touch.endY = e.changedTouches[0].clientY;

        // タップと判定するための条件:
        // 1. 移動距離が10px以内
        // 2. タップ時間が300ms以内
        const moveX = Math.abs(touch.endX - touch.startX);
        const moveY = Math.abs(touch.endY - touch.startY);
        const moveTime = Date.now() - touch.startTime;

        if (moveX < 10 && moveY < 10 && moveTime < 300) {
            // タップと判定: タップした要素またはその親がimageCardかを判断
            let targetElement = touch.element;
            let isCard = false;

            // タップした要素またはその親がimageCardかを探索
            while (targetElement && !isCard) {
                if (targetElement.classList && targetElement.classList.contains('image-card')) {
                    isCard = true;
                    showModal(targetElement);
                    break;
                }
                targetElement = targetElement.parentElement;
            }
        }
    });

    // Xボタンでモーダルを閉じる
    closeModal.addEventListener('click', (e) => {
        e.stopPropagation();
        hideModal();
    });

    // モーダル背景をクリックで閉じる
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            hideModal();
        }
    });

    // ESCキーでモーダルを閉じる
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'block') {
            hideModal();
        }
    });
});
