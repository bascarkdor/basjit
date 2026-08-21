document.addEventListener('DOMContentLoaded', function() {
        const productModal = document.getElementById('addProductModal');
        const openProductBtn = document.getElementById('addProductBtn');
        const closeProductBtn = document.getElementById('cancelAddProduct'); // Using cancel button to close
        const imageInput = document.getElementById('imageInput');
        const imagePreview = document.getElementById('imagePreview');

        // Open Modal
        openProductBtn.addEventListener('click', () => {
            productModal.showModal();
        });

        // Close Modal
        closeProductBtn.addEventListener('click', () => {
            productModal.close();
        });

        // Image Preview Logic
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                imagePreview.src = URL.createObjectURL(file);
                imagePreview.classList.remove('hidden'); // Show the image
            }
        });
    });