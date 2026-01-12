frappe.ui.form.on('Helcim Settings', {

  onload(frm) {
        if (frm.local_only_control) return;

        const wrapper = frm.fields_dict.api_url.wrapper;

        frm.local_only_control = frappe.ui.form.make_control({
            parent: wrapper,
            df: {
                fieldname: 'device_code',
                label: 'Device Code (Stored locally)',
                fieldtype: 'Data'
            },
            render_input: true
        });

        // Load from localStorage
        const key = `helcim_settings:device_code`;
        const value = localStorage.getItem(key);

        if (value) {
            frm.local_only_control.set_value(value);
        }

    },

    before_save(frm) {
        if (!frm.local_only_control) return;

        const key = `helcim_settings:device_code`;
        const value = frm.local_only_control.get_value() || '';

        localStorage.setItem(key, value);
  }

});
