/**
 * Created with PyCharm.
 * User: rhyanarthur
 * Date: 2013-08-07
 * Time: 1:05 PM
 * To change this template use File | Settings | File Templates.
 */

YUI.add('custom', function(Y) {
    Y.Custom = {
        messageBox: function(message, header) {
            var panel = new Y.Panel({
                modal: true,
                bodyContent: message,
                headerContent: header,
                centered: true,
                zIndex: 100
            });
            var okButton = {
                value: "OK",
                action: function(e) {
                    e.preventDefault();
                    panel.destroy();
                },
                section: Y.WidgetStdMod.FOOTER
            };
            panel.addButton(okButton);
            return panel;
        }
    };
}, '0.0.1', {
    requires: ['node', 'event', 'panel']
});
