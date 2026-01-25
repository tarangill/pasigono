erpnext.PointOfSale.HelcimTerminal = function(){
	var connectiontoken = "";
	var terminal;
	var loading_dialog, connection_dialog, message_dilaog, confirm_dialog;
	var payment_object,is_online;
	var me = this;
	var device_id;

	this.assign_stripe_connection_token = function(payment, dev_id, is_onl) {
		payment_object = payment;
		is_online = is_onl;
		device_id = dev_id;
		console.log("starting payment object:", payment)

		init_connection();
	}

	init_connection = function() {
		if(!device_id || device_id.length != 4) {
			show_connection_dialog('Device Code must be 4 letters (in Helcim Setting).')
			return ;
		}

		show_connection_dialog('Please Wait<br>Connecting to Helcim Terminal');
		frappe.dom.freeze();
		frappe.call({
			method: "pasigono.pasigono.pos.ping_device",
			args: { device_id: device_id},
			freeze: true,
			callback: function (r) {
				if (r.message) {
					if(r.message.success) {
						show_connection_dialog("Connected successfully.");
						frappe.dom.unfreeze();
						connection_dialog.hide();
						setTimeout(() => {
								connection_dialog.hide();
							},
							300);
					} else {
						show_connection_dialog(r.message.error);
					}
				} else {
					show_connection_dialog('Please configure the helcim settings.');
				}
			}
		});
	}


	function show_loading_modal(title, message) {
		if(loading_dialog) {
			loading_dialog.hide();
			var old = loading_dialog;
			setTimeout(() => {
				old.hide();
			}, 300)
		}

		loading_dialog = new frappe.ui.Dialog({
			title: title,
			fields: [{
					label: '',
					fieldname: 'show_dialog',
					fieldtype: 'HTML'
				},
			],
		});
		var html = '<div style="min-height:200px;position: relative;text-align: center;padding-top: 75px;line-height: 25px;font-size: 15px;">';
		html += '<div style="">' + message + '</div>';
		html += '</div>';
		loading_dialog.title = title;
		loading_dialog.fields_dict.show_dialog.$wrapper.html(html);
		loading_dialog.show();
	}


	this.collecting_payments = function(payment, is_online) {
		if(payment.frm.doc.is_return == 1){
			// confirm_dialog = new frappe.ui.Dialog({
			// 	title: 'Confirm, refund through Stripe',
			// 	fields: [{
			// 			label: '',
			// 			fieldname: 'show_dialog',
			// 			fieldtype: 'HTML'
			// 		},
			// 	],
			// 	primary_action_label: "Confirm",
			// 	primary_action(values) {
			// 		confirm_dialog.hide();
			// 		refund_payment(payment, is_online);
			// 	},
			// 	secondary_action_label: "Cancel",
			// 	secondary_action(values) {
			// 		confirm_dialog.hide();
			// 	}
			// });
			// var html = '<div style="text-align: center;">Please confirm. Refund of ' + payment.frm.doc.currency.toUpperCase() + ' ';
			// html += payment.frm.doc.grand_total * -1 + ' through stripe.</div>';
			// confirm_dialog.fields_dict.show_dialog.$wrapper.html(html);
			// confirm_dialog.show();
		}
		else{
			create_payment(payment, is_online);
		}
	}
	
	
	function refund_payment(payment, is_online){
		show_loading_modal('Refunding Payments', 'Please Wait<br>Refunding Payments');
		frappe.dom.freeze();
		var payments = payment.frm.doc.payments;
		payments.forEach(function(row){
			if(row.mode_of_payment == window.stripe_mode_of_payment){
				frappe.call({
					method: "pasigono.pasigono.api.refund_payment",
					freeze: true,
					args: {
						"payment_intent_id": row.card_payment_intent,
						"amount": row.base_amount.toFixed(2)*-100
					},
					headers: {
						"X-Requested-With": "XMLHttpRequest"
					},
					callback: function(result){
						loading_dialog.hide();
						frappe.dom.unfreeze();
						if (is_online) {
							payment.frm.savesubmit()
								.then((sales_invoice) => {
									if (sales_invoice && sales_invoice.doc) {
										payment.frm.doc.docstatus = sales_invoice.doc.docstatus;
										frappe.show_alert({
											indicator: 'green',
											message: __(`POS invoice ${sales_invoice.doc.name} created succesfully`)
										});
										payment.toggle_components(false);
										payment.order_summary.toggle_component(true);
										payment.order_summary.load_summary_of(payment.frm.doc, true);
									}
								});

						} else {
							payment.payment.events.submit_invoice();
						}
					}
				});
			}
		});
	}
	
	
	function create_payment(payment, is_online){
		show_loading_modal('Collecting Payments' + Date.now(), 'Please Wait<br>Sending Payment request to Helcim Terminal');

		frappe.dom.freeze();
		frappe.call({
			method: "pasigono.pasigono.pos.start_purchase",
			freeze: true,
			args: {
				"device_id": device_id,
				"pos_invoice_id": payment.frm.doc.name,
				"amount": payment.frm.doc.grand_total,
				"currency": payment.frm.doc.currency
			},
			error: function(r) {
				frappe.dom.unfreeze();
				setTimeout(() => {
					loading_dialog.hide();
				}, 300)
				show_error_dialog("There was an error while contacting Helcim for payment.")
			},
			callback: function (r) {
				if(!r.message.success) {
					frappe.dom.unfreeze();
					console.log("error:", r)
					setTimeout(() => {
						loading_dialog.hide();
					}, 300)
					show_error_dialog('Error contacting Helcim for payment<br />' + r.message.error);
				} else {
					console.log("response:", r)
					setTimeout(() => {
						loading_dialog.hide();
					}, 300)
					confirm_dialog = new frappe.ui.Dialog({
						title: 'Waiting for Credit Card Payment',
						fields: [{
								label: '',
								fieldname: 'show_dialog',
								fieldtype: 'HTML'
							},
						]
					});
					var html = '<div style="text-align: center;">Waiting for the customer to complete payment of ' + payment.frm.doc.currency + ' ';
					html += payment.frm.doc.grand_total + ' through Helcim.</div>';
					confirm_dialog.fields_dict.show_dialog.$wrapper.html(html);
					confirm_dialog.show();
					frappe.realtime.on(`helcim_payment_${r.message.invoice}`, (data) => {
						console.log(data);
						frappe.dom.unfreeze();
						if (data.status === "Cancelled") {
							confirm_dialog.hide();
						} else if (data.status === "Approved") {
							capture_payment(payment, is_online, r.message.invoice);
						} else if (data.status === "Declined") {
							frappe.msgprint("Payment Declined");
						} else {
							console.log("Unknown payment status!")
						}
					});
				}
			}
		})
	}
		
	function capture_payment(payment, is_online, invoiceNumber){
		console.log("will capture payment for invoiceNumber:", invoiceNumber)
		confirm_dialog.hide();
		var payments = payment.frm.doc.payments;
		payments.forEach(function(row){
			if(row.mode_of_payment == window.helcim_mode_of_payment){
				row.helcim_transaction = invoiceNumber;
			}
		});

		if (is_online) {
			payment.frm.savesubmit()
				.then((sales_invoice) => {
					//For raw printing
					if(window.open_cash_drawer_automatically == 1){
						payment.payment.events.open_cash_drawer();
					}
					
					if(window.automatically_print == 1){
						payment.payment.events.raw_print(this.frm);							
					}
					
					if (sales_invoice && sales_invoice.doc) {
						payment.frm.doc.docstatus = sales_invoice.doc.docstatus;
						// frappe.show_alert({
						// 	indicator: 'green',
						// 	message: __(`POS invoice ${sales_invoice.doc.name} created succesfully`)
						// });
						payment.toggle_components(false);
						payment.order_summary.toggle_component(true);
						payment.order_summary.load_summary_of(payment.frm.doc, true);
					}
				});
		} else {
			payment.payment.events.submit_invoice();
		}
	}
	
	function retry_stripe_terminal(me, payment_object, is_online)
	{
		me.collecting_payments(payment_object, is_online);
	}

	function change_payment_method()
	{
		$(".num-col.brand-primary").click();
	}
	
	function show_connection_dialog(message) {
		if(!connection_dialog) {
			connection_dialog = new frappe.ui.Dialog({
				title: 'Connecting to Helcim Terminal',
				fields: [{
						label: '',
						fieldname: 'show_dialog',
						fieldtype: 'HTML'
					},
				],
				// primary_action_label: "Retry",
				// primary_action(values) {
				// 	init_connection();
				// 	connection_dialog.hide();
				// }
			});
		}
		var html = "<p>" + message + "</p>";
		connection_dialog.fields_dict.show_dialog.$wrapper.html(html);
		connection_dialog.show();
	}

	function show_error_dialog(message) {
			message_dilaog = new frappe.ui.Dialog({
				title: 'Error',
				fields: [{
						label: '',
						fieldname: 'show_dialog',
						fieldtype: 'HTML'
					},
				],
				primary_action_label: "Retry",
				primary_action(values) {
					retry_stripe_terminal(me, payment_object, is_online);
					message_dilaog.hide();
				}
			});
		var html = "<p>" + message + "</p>";
		message_dilaog.fields_dict.show_dialog.$wrapper.html(html);
		message_dilaog.show();
	}

	function show_payment_error_dialog(message) {
		message_dilaog = new frappe.ui.Dialog({
			title: 'Message',
			fields: [{
					label: '',
					fieldname: 'show_dialog',
					fieldtype: 'HTML'

				},

			],
			primary_action_label: "Retry",
			secondary_action_label: "Change Payment Mode",
			primary_action(values) {
				retry_stripe_terminal(me, payment_object, is_online);
				message_dilaog.hide();
			},
			secondary_action(values) {
				change_payment_method();
				message_dilaog.hide();
			}
		});
		var html = "<p>" + message + "</p>";
		message_dilaog.fields_dict.show_dialog.$wrapper.html(html);
		message_dilaog.show();
	}
}
