    const modal = document.getElementById('categoryModal');
    const openBtn = document.getElementById('addCategoryBtn');
    const closeBtn = document.getElementById('closeModal');

    openBtn.addEventListener('click', () => modal.showModal());
    closeBtn.addEventListener('click', () => modal.close());