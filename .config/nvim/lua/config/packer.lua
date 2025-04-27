-- This file can be loaded by calling `lua require('plugins')` from your init.vim

-- Only required if you have packer configured as `opt`
vim.cmd [[packadd packer.nvim]]

return require('packer').startup(function(use)
	-- Packer can manage itself
	use 'wbthomason/packer.nvim'

	use {
		'nvim-telescope/telescope.nvim', tag = '0.1.8',
		-- or                            , branch = '0.1.x',
		requires = { {'nvim-lua/plenary.nvim'} }
	}
	
	-- lua/plugins/rose-pine.lua
	use({
		"rose-pine/neovim",
		as = "rose-pine",
		config = function()
			vim.cmd("colorscheme rose-pine")
		end
	})

	-- use {
	-- 	'rktjmp/lush.nvim',
	-- 	config = function()
	-- 		require'lush'.from_file("/home/simon/Downloads/desktop-1920x1080.jpg")
	-- 	end
	-- }
	--
	use ('nvim-treesitter/nvim-treesitter', {run= ':TSUpdate'})
	use ('nvim-treesitter/playground')
	use ('ThePrimeagen/harpoon')
	use 'mbbill/undotree'
end)

