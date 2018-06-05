import React, { Component } from "react";
import { gql, graphql } from "react-apollo";
import { withRouter, Link } from "react-router-dom";

import Header from "../Header";
import Footer from "../Footer";

class LogIn extends Component {
    constructor(props, context) {
        super(props, context);
        this.state = {
            form: { email: "", password: "" },
            failed: false,
            busy: false
        };
    }

    handleChange(field, event) {
        let form = { ...this.state.form };
        form[field] = event.target.value;
        this.setState({ form: form });
    }

    /**
     * Handle login
     */
    handleSubmit = () => {
        if (this.state.busy) return;
        this.setState({ failed: false, busy: true });
        this.props
            .mutate({ variables: { ...this.state.form } })
            .then(({ data: { login } }) => {
                if (login.success) {
                    //  success
                    localStorage.setItem("user", JSON.stringify(login.user));
                    this.props.history.push("/");
                } else {
                    //  failed
                    this.setState({ busy: false, failed: true });
                }
            })
            .catch(error => {
                console.warn("there was an error sending the query", error);
                this.setState({ errors: [error.graphQLErrors[0].message] });
            });
    };

    render() {
        return (
            <div id="signup" className="login">
                <Header />
                <div className="body-wrapper">
                    <div className="body">
                        <h3 className="text-center">Sign In</h3>

                        {this.state.failed && (
                            <div className="alert alert-danger">Invalid login credentials</div>
                        )}

                        <div className="form-group email">
                            <input
                                onChange={e => this.handleChange("email", e)}
                                type="email"
                                placeholder="Email address"
                                className="form-control"
                            />
                        </div>
                        <div className="form-group">
                            <input
                                onChange={e => this.handleChange("password", e)}
                                type="password"
                                placeholder="Password"
                                className="form-control"
                            />
                            <p>
                                <u>Forgot password</u>
                            </p>
                        </div>
                        <div className="form-group text-center">
                            <button onClick={this.handleSubmit}>SIGN IN</button>
                        </div>
                        <div className="form-group text-center border">
                            <h4>Do not have an account?</h4>
                            <Link to="/signup">
                                <u>Sign up - 100% free</u>
                            </Link>
                        </div>
                    </div>
                </div>
                <Footer />
            </div>
        );
    }
}

//  GraphQL mutation
const submitQuery = gql`
    mutation($email: String!, $password: String!) {
        login(email: $email, password: $password) {
            success
            user {
                id
                firstName
                lastName
                email
                token
            }
        }
    }
`;

const login = graphql(submitQuery)(LogIn);

export default withRouter(login);
