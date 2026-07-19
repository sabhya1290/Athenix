const User = require("../models/User");

const getProfile = async (req, res) => {

    res.json({
        success: true,
        user: req.user
    });

};

const updateProfile = async (req, res) => {

    try {

        const user = await User.findById(req.user._id);

        if (!user) {
            return res.status(404).json({
                success:false,
                message:"User not found"
            });
        }

        user.name = req.body.name || user.name;

        if(req.body.password){
            user.password = req.body.password;
        }

        await user.save();
        const updatedUser = await User.findById(user._id).select("-password");

        res.json({
            success:true,
            message:"Profile Updated",
            user: updatedUser,
        });

    } catch (error) {

        res.status(500).json({
            success:false,
            message:error.message
        });

    }

};

module.exports = {
    getProfile,
    updateProfile
};