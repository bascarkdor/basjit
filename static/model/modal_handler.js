// static/model/modal_handler.js

const modal = document.getElementById('universalModal');
const form = document.getElementById('universalForm');
const modalTitle = document.getElementById('modalTitle');
const modalContent = document.getElementById('modalContent');

// 1. Upgraded Config Object
const entityConfigs = {
    product: {
        title: "Product",
        url: '/admin/product',
        fields: [
            { name: 'name', type: 'text', label: 'Product Name' },
            { name: 'Image', type: 'text', label: 'Image' },
            { name: 'category', type: 'text', label: 'Category' },
            { name: 'price', type: 'number', label: 'Price' },
            { name: 'stock', type: 'number', label: 'Stock' }
        ]
    },
    user: {
        title: "User",
        url: '/admin/users',
        customHtml: `
            <div class="flex items-center gap-4 mb-2">
                <img id="avatarPreview" src="https://ui-avatars.com/api/?name=User" class="w-16 h-16 rounded-full object-cover border border-slate-200 shadow-sm">
                <div class="flex-1">
                    <label class="block text-sm font-medium text-slate-700 mb-1">Upload Photo</label>
                    <input type="file" id="avatarInput" accept="image/*" class="w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer">
                </div>
            </div>
        `,
        fields: [
            { name: 'name', type: 'text', label: 'Full Name' },
            { name: 'email', type: 'email', label: 'Email Address' },
            { name: 'role', type: 'select', label: 'Role', options: ['Administrator', 'Editor', 'Viewer'] }
        ]
    }
};

window.openModal = (type, data = null) => {
    const config = entityConfigs[type];
    const isEdit = data !== null;

    modalTitle.innerText = isEdit ? `Edit ${config.title}` : `Add New ${config.title}`;
    form.action = isEdit ? `${config.baseAction}/edit/${data.id}` : `${config.baseAction}/add`;

    // 1. Generate standard inputs from fields array
    modalContent.innerHTML = config.fields.map(field => `
        <div>
            <label class="block text-sm font-medium text-slate-700">${field.label}</label>
            <input type="${field.type}" name="${field.name}" 
                   value="${isEdit ? (data[field.name] || '') : ''}" 
                   required class="w-full px-3 py-2 border border-slate-300 rounded-lg">
        </div>
    `).join('');

    // 2. Inject Image Section
    modalContent.insertAdjacentHTML('afterbegin', `
        <div class="flex items-center gap-4 mb-4">
            <img id="imagePreview" src="${(isEdit && data.image) ? data.image : ''}" 
                 class="w-16 h-16 rounded-lg object-cover border border-slate-200 ${isEdit ? '' : 'hidden'}">
            <div class="flex-1">
                <label class="block text-sm font-medium text-slate-700 mb-1">Product Image</label>
                <input type="file" name="product_image" id="imageInput" accept="image/*" 
                       class="w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer">
            </div>
        </div>
    `);

    // 3. Attach image preview listener
    document.getElementById('imageInput').addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            document.getElementById('imagePreview').src = URL.createObjectURL(file);
            document.getElementById('imagePreview').classList.remove('hidden');
        }
    });

    modal.showModal();
};