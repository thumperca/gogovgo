import React, { Component } from "react";

import Header from "../Header";
import Footer from "../Footer";

class SignUp extends Component {
    constructor(props, context) {
        super(props, context);
        this.state = {
            states: []
        };
    }

    componentDidMount() {
        fetch("/api/countries/")
            .then(res => res.json())
            .then(data => this.setState({ states: data.states }));
    }
    render() {
        return (
            <div id="signup">
                <Header />
                <div className="body">
                    <h3 className="text-center">Sign Up</h3>
                    <div className="form-group">
                        <label>Name</label>
                        <p>Your name will be kept private, and NOT published online.</p>
                        <input
                            type="text"
                            placeholder="Insert your name"
                            className="form-control"
                        />
                    </div>
                    <div className="form-group">
                        <label>Username</label>
                        <p>Your username is public, and WILL be published online.</p>
                        <input
                            type="text"
                            placeholder="Insert your username"
                            className="form-control"
                        />
                    </div>
                    <div className="form-group">
                        <label>Email</label>
                        <input
                            type="email"
                            placeholder="Insert your email"
                            className="form-control"
                        />
                    </div>
                    <div className="form-group">
                        <label>Password</label>
                        <input
                            type="password"
                            placeholder="Insert your password"
                            className="form-control"
                        />
                    </div>
                    <div className="form-group">
                        <label>Select your country</label>
                        <select className="form-control">
                            <option>Select your country</option>
                            {this.state.states.map((state, index) => {
                                return <option key={index}>{state.long}</option>;
                            })}
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Zip code</label>
                        <input type="text" placeholder="Insert Zip code" className="form-control" />
                    </div>
                    <div className="form-group text-center">
                        <button>SIGN UP - 100% FREE</button>
                        <p className="terms">
                            By creating an account, you agree to the <u>terms of participation</u>{" "}
                            and <u>privacy policy</u>
                        </p>
                    </div>
                    <div className="form-group text-center border">
                        <h4>Already have an account?</h4>
                        <a href="/login">
                            <u>Sign in</u>
                        </a>
                    </div>
                </div>
                <Footer />
            </div>
        );
    }
}

export default SignUp;
