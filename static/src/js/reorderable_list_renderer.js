/** @odoo-module */

import { ListRenderer } from "@web/views/list/list_renderer"
import { registry } from "@web/core/registry";

const ReorderableListRenderer = ListRenderer.extend({
    init(){
        this._super(...arguments);
        this.columnReorderingEnabled = true;
    },

    _onColumnsReordered(newOrder){
         const key = `list_order_${this.state.model}`;
        localStorage.setItem(key, JSON.stringify(newOrder));
    },
    _computeColumns(params) {
        let cols = this._super(...arguments);
        const key = `list_order_${this.state.model}`;
        const savedOrder = localStorage.getItem(key);

        if (savedOrder) {
            const order = JSON.parse(savedOrder);
            cols = order.map(index => cols[index]).filter(Boolean);
        }
        return cols;
    },
});

registry.category("views").add("reorderable_list", {
    ...registry.category("views").get("list"),
    Renderer: ReorderableListRenderer,
});