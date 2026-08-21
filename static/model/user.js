// static/model/user.js
window.userConfig = {
    title: "User",
    baseUrl: "/admin/users",
    fields: [
        { name: 'name', label: 'Full Name', type: 'text' },
        { name: 'email', label: 'Email Address', type: 'email' },
        { name: 'role', label: 'Role', type: 'select', options: ['Administrator', 'Editor', 'Viewer'] }
    ],
    customHtml: `
        <div class="flex items-center gap-4 mb-2">
            <img id="avatarPreview" src="https://ui-avatars.com/api/?name=User" class="w-16 h-16 rounded-full object-cover border border-slate-200 shadow-sm">
            <div class="flex-1">
                <label class="block text-sm font-medium text-slate-700 mb-1">Upload Photo</label>
                <input type="file" id="avatarInput" accept="image/*" class="w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer">
            </div>
        </div>
    `
};