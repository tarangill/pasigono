frappe.ui.form.on('Helcim Settings', {
    refresh: function(frm) {
        frm.add_custom_button(__('Ping Device'), async function() {
            const key = `helcim_settings:device_code`;
            const value = frm.local_only_control.get_value() || '';
            const finalValue = value.trim();
            
            if(finalValue.length !=4 ){
                frappe.msgprint("Device Code must be 4 letters.");
                return ;
            } else {
                const res = await frappe.call({
                    method: "pasigono.pasigono.pos.ping_device",
                    args: { device_id: finalValue}
                });

                if(res.message.success) {
                    frappe.msgprint("Ping sent successfully.");
                } else {
                    frappe.msgprint(res.message.error);
                }
            }
        });
    },

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
        const finalValue = value.trim();
        
        if(finalValue.length !=4 ){
            frappe.msgprint("Device Code must be 4 letters.");
            return ;
        }

        localStorage.setItem(key, finalValue);
  }

});
