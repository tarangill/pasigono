frappe.ui.form.on('Clover Settings', {
    refresh: function(frm) {
        frm.add_custom_button(__('Authorize Clover Account'), async function() {
            const res = await frappe.call({
                method: "pasigono.clover.oauth.url"
            });

            // frappe.msgprint(res?.message?.auth_url);
            window.location = res?.message?.auth_url;
        })

        frm.add_custom_button(__('Get Devices'), async function() {
            const res = await frappe.call({
                method: "pasigono.clover.pos.get_devices"
            });

            frappe.msgprint(res?.message?.join(", "));
            // window.location = res?.message?.auth_url;
        })

        frm.add_custom_button(__('Ping Device'), async function() {
            const value = frm.local_only_control.get_value() || '';
            const finalValue = value.trim();
            
            if(finalValue.length < 1 ){
                frappe.msgprint("A valid device ID is needed.");
                return ;
            } else {
                const res = await frappe.call({
                    method: "pasigono.clover.pos.ping_device",
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

        const wrapper = frm.fields_dict.app_secret.wrapper;

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
        const key = `clover_settings:device_code`;
        const value = localStorage.getItem(key);

        if (value) {
            frm.local_only_control.set_value(value);
        }

    },

    before_save(frm) {
        if (!frm.local_only_control) return;

        const key = `clover_settings:device_code`;
        const value = frm.local_only_control.get_value() || '';
        const finalValue = value.trim();
        
        // if(finalValue.length < 1 ){
        //     frappe.msgprint("Please enter a valid device code.");
        //     return ;
        // }

        localStorage.setItem(key, finalValue);
    }

});
