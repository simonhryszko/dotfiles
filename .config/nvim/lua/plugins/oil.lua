return {
	"stevearc/oil.nvim",
	dependencies = { "nvim-tree/nvim-web-devicons" },
	config = function()
		require("oil").setup({
      default_file_explorer = true, -- start up nvim with oil instead of netrw
			columns = { },
			keymaps = {
				["<C-h>"] = false,
        ["<C-c>"] = false, -- prevent from closing Oil as <C-c> is esc key
				["<M-h>"] = "actions.select_split", -- open in selected as hor split
        ["q"] = "actions.close",
			},
      delete_to_trash = true,
			view_options = {
				show_hidden = true,
			},
      skip_confirm_for_simple_edits = true,
		})

		vim.keymap.set("n", "-", "<CMD>Oil<CR>", { desc = "Open parent directory" })
		vim.keymap.set("n", "<leader>-", require("oil").toggle_float, { desc = "open parent dir in float window" })

    vim.api.nvim_create_autocmd("FileType", {
      pattern = "oil", -- Adjust if Oil uses a specific file type identifier
      callback = function()
        vim.opt_local.cursorline = true
      end,
    })
  end,

}
